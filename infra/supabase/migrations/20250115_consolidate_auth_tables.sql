-- Migration: Consolidate auth tables into identity.users
-- This migration consolidates identity.auth_users and identity.auth_sessions into identity.users table
-- Date: 2025-01-15

-- Step 1: Add new columns to identity.users
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS provider_user_id VARCHAR(255) UNIQUE;
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS provider_email VARCHAR(320);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS provider_metadata JSONB DEFAULT '{}';
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS job_title VARCHAR(100);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS organization_name VARCHAR(100);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS last_login_date TIMESTAMPTZ;
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS last_login_location VARCHAR(255);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50);
ALTER TABLE identity.users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';

-- Make password nullable for external auth users
ALTER TABLE identity.users ALTER COLUMN password DROP NOT NULL;

-- Step 2: Add avatar_url to organizations
ALTER TABLE org.organizations ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);

-- Step 3: Migrate data from auth_users to users (if auth_users table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'identity' AND tablename = 'auth_users') THEN
        UPDATE identity.users u
        SET
            provider_user_id = au.provider_user_id,
            provider_type = au.provider_type,
            provider_email = au.provider_email,
            provider_metadata = au.provider_metadata
        FROM identity.auth_users au
        WHERE u.id = au.local_user_id;
    END IF;
END $$;

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_provider_user_id
ON identity.users(provider_user_id)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_users_provider_type
ON identity.users(provider_type)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_users_last_login_date
ON identity.users(last_login_date DESC)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_organizations_avatar_url
ON org.organizations(avatar_url)
WHERE avatar_url IS NOT NULL AND deleted_at IS NULL;

-- Step 5: Create function to sync users from auth.users
CREATE OR REPLACE FUNCTION identity.sync_user_from_auth()
RETURNS TRIGGER AS $$
DECLARE
    existing_user_id UUID;
BEGIN
    -- Check if user already exists
    SELECT id INTO existing_user_id
    FROM identity.users
    WHERE provider_user_id = NEW.id::text;

    IF existing_user_id IS NULL THEN
        -- Create new user
        INSERT INTO identity.users (
            id,
            email,
            first_name,
            last_name,
            provider_user_id,
            provider_type,
            provider_email,
            provider_metadata,
            created_at,
            updated_at,
            created_by,
            updated_by
        ) VALUES (
            gen_random_uuid(),
            NEW.email,
            COALESCE(NEW.raw_user_meta_data->>'first_name', split_part(NEW.email, '@', 1)),
            COALESCE(NEW.raw_user_meta_data->>'last_name', 'User'),
            NEW.id::text,
            'supabase',
            NEW.email,
            jsonb_build_object('supabase_data', NEW.raw_user_meta_data),
            NOW(),
            NOW(),
            gen_random_uuid(), -- Temporary, will be updated
            gen_random_uuid()  -- Temporary, will be updated
        ) RETURNING id INTO existing_user_id;

        -- Update audit fields to self-reference
        UPDATE identity.users
        SET created_by = existing_user_id,
            updated_by = existing_user_id
        WHERE id = existing_user_id;
    ELSE
        -- Update existing user metadata
        UPDATE identity.users
        SET
            provider_metadata = jsonb_build_object('supabase_data', NEW.raw_user_meta_data),
            updated_at = NOW()
        WHERE id = existing_user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 6: Create trigger for auth.users insert/update
DROP TRIGGER IF EXISTS sync_auth_user_trigger ON auth.users;
CREATE TRIGGER sync_auth_user_trigger
AFTER INSERT OR UPDATE ON auth.users
FOR EACH ROW EXECUTE FUNCTION identity.sync_user_from_auth();

-- Step 7: Sync existing auth.users to identity.users
INSERT INTO identity.users (
    email,
    first_name,
    last_name,
    provider_user_id,
    provider_type,
    provider_email,
    provider_metadata,
    created_at,
    updated_at,
    created_by,
    updated_by
)
SELECT
    au.email,
    COALESCE(au.raw_user_meta_data->>'first_name', split_part(au.email, '@', 1)),
    COALESCE(au.raw_user_meta_data->>'last_name', 'User'),
    au.id::text,
    'supabase',
    au.email,
    jsonb_build_object('supabase_data', au.raw_user_meta_data),
    COALESCE(au.created_at, NOW()),
    COALESCE(au.updated_at, NOW()),
    gen_random_uuid(), -- Will be updated
    gen_random_uuid()  -- Will be updated
FROM auth.users au
WHERE NOT EXISTS (
    SELECT 1 FROM identity.users u
    WHERE u.provider_user_id = au.id::text
);

-- Update audit fields for newly inserted users
UPDATE identity.users
SET created_by = id, updated_by = id
WHERE created_by NOT IN (SELECT id FROM identity.users WHERE id != created_by);

-- Step 8: Drop old tables (after verifying migration success)
-- IMPORTANT: Only run these after confirming data migration is successful!
-- DROP TABLE IF EXISTS identity.auth_sessions CASCADE;
-- DROP TABLE IF EXISTS identity.auth_users CASCADE;

-- Step 9: Add comments for documentation
COMMENT ON COLUMN identity.users.provider_user_id IS 'ID from the authentication provider (e.g., Supabase auth.users.id)';
COMMENT ON COLUMN identity.users.provider_type IS 'Type of authentication provider (supabase, auth0, clerk, etc.)';
COMMENT ON COLUMN identity.users.provider_email IS 'Email address from the authentication provider';
COMMENT ON COLUMN identity.users.provider_metadata IS 'Additional metadata from the authentication provider';
COMMENT ON COLUMN identity.users.avatar_url IS 'URL to the user''s avatar image';
COMMENT ON COLUMN identity.users.phone IS 'User''s phone number';
COMMENT ON COLUMN identity.users.job_title IS 'User''s job title';
COMMENT ON COLUMN identity.users.organization_name IS 'Name of user''s organization (for display purposes)';
COMMENT ON COLUMN identity.users.last_login_date IS 'Timestamp of user''s last login';
COMMENT ON COLUMN identity.users.last_login_location IS 'Location of user''s last login (IP or geographic)';
COMMENT ON COLUMN identity.users.timezone IS 'User''s preferred timezone';
COMMENT ON COLUMN identity.users.preferences IS 'User preferences and settings';
COMMENT ON COLUMN org.organizations.avatar_url IS 'URL to the organization''s avatar image';

-- Migration complete message
DO $$
BEGIN
    RAISE NOTICE 'Auth table consolidation migration completed successfully';
    RAISE NOTICE 'Remember to drop identity.auth_sessions and identity.auth_users tables after verification';
END $$;
