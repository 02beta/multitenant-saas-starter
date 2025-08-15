-- ============================================================================
-- BASELINE FUNCTIONS AND TRIGGERS
-- This file contains all functions and triggers for the application
-- No table alterations - assumes tables are created with proper structure
-- ============================================================================

-- ============================================================================
-- SECTION 1: AUTH SYNC FUNCTIONS
-- ============================================================================

-- Function to sync users from Supabase auth.users to identity.users
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
            is_active,
            is_superuser,
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
            true,
            false,
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

-- Trigger to sync auth.users changes to identity.users
DROP TRIGGER IF EXISTS sync_auth_user_trigger ON auth.users;
CREATE TRIGGER sync_auth_user_trigger
AFTER INSERT OR UPDATE ON auth.users
FOR EACH ROW EXECUTE FUNCTION identity.sync_user_from_auth();

-- ============================================================================
-- SECTION 2: AUDIT FIELD FUNCTIONS
-- ============================================================================

-- Helper function to get current user ID from auth context
CREATE OR REPLACE FUNCTION identity.get_current_user_id()
RETURNS UUID AS $$
DECLARE
    current_user_id UUID;
    auth_user_id TEXT;
BEGIN
    -- Get the auth user ID from the current session
    auth_user_id := auth.uid()::TEXT;

    -- Look up the corresponding identity.users record
    SELECT id INTO current_user_id
    FROM identity.users
    WHERE provider_user_id = auth_user_id;

    -- Return the user ID, or NULL if not found
    RETURN current_user_id;
EXCEPTION
    WHEN OTHERS THEN
        -- If auth.uid() fails or user not found, return NULL
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger function for updating audit fields
CREATE OR REPLACE FUNCTION identity.update_audit_fields()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id UUID;
BEGIN
    -- Get the current user ID from auth context
    current_user_id := identity.get_current_user_id();

    -- Always update the updated_at timestamp
    NEW.updated_at = NOW();

    -- Update updated_by if we have a current user
    IF current_user_id IS NOT NULL THEN
        NEW.updated_by = current_user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger function for soft delete
CREATE OR REPLACE FUNCTION identity.handle_soft_delete()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id UUID;
BEGIN
    -- Only act if deleted_at is being set from NULL to a value
    IF NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL THEN
        -- Get the current user ID from auth context
        current_user_id := identity.get_current_user_id();

        -- Set deleted_by if we have a current user
        IF current_user_id IS NOT NULL THEN
            NEW.deleted_by = current_user_id;
        ELSE
            -- Fallback to updated_by if no current user
            NEW.deleted_by = COALESCE(NEW.updated_by, OLD.updated_by);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger function for insert (sets created_by and updated_by)
CREATE OR REPLACE FUNCTION identity.set_initial_audit_fields()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id UUID;
BEGIN
    -- Get the current user ID from auth context
    current_user_id := identity.get_current_user_id();

    -- Set timestamps if not already set
    IF NEW.created_at IS NULL THEN
        NEW.created_at = NOW();
    END IF;

    IF NEW.updated_at IS NULL THEN
        NEW.updated_at = NOW();
    END IF;

    -- Set created_by and updated_by if we have a current user
    IF current_user_id IS NOT NULL THEN
        IF NEW.created_by IS NULL THEN
            NEW.created_by = current_user_id;
        END IF;
        IF NEW.updated_by IS NULL THEN
            NEW.updated_by = current_user_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Special trigger function for identity.users table (self-reference on create)
CREATE OR REPLACE FUNCTION identity.set_user_self_audit_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- For new user records, set audit fields to self-reference
    IF NEW.created_by IS NULL THEN
        NEW.created_by = NEW.id;
    END IF;

    IF NEW.updated_by IS NULL THEN
        NEW.updated_by = NEW.id;
    END IF;

    -- Set timestamps if not already set
    IF NEW.created_at IS NULL THEN
        NEW.created_at = NOW();
    END IF;

    IF NEW.updated_at IS NULL THEN
        NEW.updated_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SECTION 3: UTILITY FUNCTIONS
-- ============================================================================

-- Function placeholder for session cleanup
-- Note: Sessions are now managed in application memory or external cache
-- This function is kept for backwards compatibility but returns 0
CREATE OR REPLACE FUNCTION identity.cleanup_expired_sessions()
RETURNS INTEGER AS $$
BEGIN
    -- Sessions are no longer stored in database
    -- This function is a no-op for backwards compatibility
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- Helper function to manually set audit fields (for migrations/scripts)
CREATE OR REPLACE FUNCTION identity.set_audit_fields_for_user(
    p_table_schema TEXT,
    p_table_name TEXT,
    p_record_id UUID,
    p_user_id UUID,
    p_action TEXT DEFAULT 'update' -- 'insert', 'update', or 'delete'
)
RETURNS VOID AS $$
DECLARE
    query TEXT;
BEGIN
    IF p_action = 'insert' THEN
        query := format(
            'UPDATE %I.%I SET created_by = $1, updated_by = $1, created_at = NOW(), updated_at = NOW() WHERE id = $2',
            p_table_schema, p_table_name
        );
    ELSIF p_action = 'delete' THEN
        query := format(
            'UPDATE %I.%I SET deleted_by = $1, deleted_at = NOW() WHERE id = $2',
            p_table_schema, p_table_name
        );
    ELSE -- update
        query := format(
            'UPDATE %I.%I SET updated_by = $1, updated_at = NOW() WHERE id = $2',
            p_table_schema, p_table_name
        );
    END IF;

    EXECUTE query USING p_user_id, p_record_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SECTION 4: TRIGGERS FOR identity.users TABLE
-- ============================================================================

-- Special trigger for users table (self-reference)
DROP TRIGGER IF EXISTS set_user_self_audit_trigger ON identity.users;
CREATE TRIGGER set_user_self_audit_trigger
BEFORE INSERT ON identity.users
FOR EACH ROW EXECUTE FUNCTION identity.set_user_self_audit_fields();

-- Update trigger for users
DROP TRIGGER IF EXISTS update_user_audit_trigger ON identity.users;
CREATE TRIGGER update_user_audit_trigger
BEFORE UPDATE ON identity.users
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION identity.update_audit_fields();

-- Soft delete trigger for users
DROP TRIGGER IF EXISTS handle_user_soft_delete_trigger ON identity.users;
CREATE TRIGGER handle_user_soft_delete_trigger
BEFORE UPDATE ON identity.users
FOR EACH ROW
WHEN (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL)
EXECUTE FUNCTION identity.handle_soft_delete();

-- ============================================================================
-- SECTION 5: TRIGGERS FOR org.organizations TABLE
-- ============================================================================

-- Insert trigger for organizations
DROP TRIGGER IF EXISTS set_organization_audit_trigger ON org.organizations;
CREATE TRIGGER set_organization_audit_trigger
BEFORE INSERT ON org.organizations
FOR EACH ROW EXECUTE FUNCTION identity.set_initial_audit_fields();

-- Update trigger for organizations
DROP TRIGGER IF EXISTS update_organization_audit_trigger ON org.organizations;
CREATE TRIGGER update_organization_audit_trigger
BEFORE UPDATE ON org.organizations
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION identity.update_audit_fields();

-- Soft delete trigger for organizations
DROP TRIGGER IF EXISTS handle_organization_soft_delete_trigger ON org.organizations;
CREATE TRIGGER handle_organization_soft_delete_trigger
BEFORE UPDATE ON org.organizations
FOR EACH ROW
WHEN (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL)
EXECUTE FUNCTION identity.handle_soft_delete();

-- ============================================================================
-- SECTION 6: TRIGGERS FOR org.memberships TABLE
-- ============================================================================

-- Insert trigger for memberships
DROP TRIGGER IF EXISTS set_membership_audit_trigger ON org.memberships;
CREATE TRIGGER set_membership_audit_trigger
BEFORE INSERT ON org.memberships
FOR EACH ROW EXECUTE FUNCTION identity.set_initial_audit_fields();

-- Update trigger for memberships
DROP TRIGGER IF EXISTS update_membership_audit_trigger ON org.memberships;
CREATE TRIGGER update_membership_audit_trigger
BEFORE UPDATE ON org.memberships
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION identity.update_audit_fields();

-- Soft delete trigger for memberships
DROP TRIGGER IF EXISTS handle_membership_soft_delete_trigger ON org.memberships;
CREATE TRIGGER handle_membership_soft_delete_trigger
BEFORE UPDATE ON org.memberships
FOR EACH ROW
WHEN (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL)
EXECUTE FUNCTION identity.handle_soft_delete();

-- ============================================================================
-- SECTION 7: FUNCTION COMMENTS
-- ============================================================================

COMMENT ON FUNCTION identity.sync_user_from_auth() IS
'Syncs Supabase auth.users records to identity.users table on insert/update';

COMMENT ON FUNCTION identity.get_current_user_id() IS
'Gets the current identity.users.id from the auth context by looking up provider_user_id';

COMMENT ON FUNCTION identity.update_audit_fields() IS
'Trigger function that automatically updates audit fields on record modification';

COMMENT ON FUNCTION identity.handle_soft_delete() IS
'Trigger function that sets deleted_by when a record is soft deleted';

COMMENT ON FUNCTION identity.set_initial_audit_fields() IS
'Trigger function that sets initial audit fields when a record is created';

COMMENT ON FUNCTION identity.set_user_self_audit_fields() IS
'Special trigger function for identity.users table that sets audit fields to self-reference';

COMMENT ON FUNCTION identity.cleanup_expired_sessions() IS
'Legacy function - sessions are now managed in application memory. Returns 0 for backwards compatibility.';

COMMENT ON FUNCTION identity.set_audit_fields_for_user(TEXT, TEXT, UUID, UUID, TEXT) IS
'Manual function to set audit fields for a specific user and record (useful for migrations)';

-- ============================================================================
-- END OF BASELINE FUNCTIONS AND TRIGGERS
-- ============================================================================
