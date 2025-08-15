-- Auth Improvements Migration
-- Fixes race conditions and adds performance indexes

-- Add unique constraint to prevent duplicate active sessions per user/organization
ALTER TABLE identity.auth_sessions
ADD CONSTRAINT unique_active_session_per_user_org
UNIQUE (local_user_id, organization_id, is_active)
WHERE is_active = true AND deleted_at IS NULL;

-- Add index for token lookups (performance optimization)
CREATE INDEX IF NOT EXISTS idx_auth_sessions_access_token
ON identity.auth_sessions(access_token)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_auth_sessions_refresh_token
ON identity.auth_sessions(refresh_token)
WHERE refresh_token IS NOT NULL AND deleted_at IS NULL;

-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_auth_users_provider_user_id
ON identity.auth_users(provider_type, provider_user_id)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_auth_users_provider_email
ON identity.auth_users(provider_email)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_users_email
ON identity.users(email)
WHERE deleted_at IS NULL;

-- Add index for session expiration queries
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at
ON identity.auth_sessions(expires_at)
WHERE is_active = true AND deleted_at IS NULL;

-- Add composite index for membership lookups
CREATE INDEX IF NOT EXISTS idx_memberships_org_user
ON org.memberships(organization_id, user_id)
WHERE deleted_at IS NULL;

-- Add index for organization slug lookups
CREATE INDEX IF NOT EXISTS idx_organizations_slug
ON org.organizations(slug)
WHERE deleted_at IS NULL;

-- Function to clean up expired sessions (can be called periodically)
CREATE OR REPLACE FUNCTION identity.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE identity.auth_sessions
    SET is_active = false,
        updated_at = CURRENT_TIMESTAMP
    WHERE expires_at < CURRENT_TIMESTAMP
    AND is_active = true
    AND deleted_at IS NULL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON FUNCTION identity.cleanup_expired_sessions() IS
'Marks expired sessions as inactive. Should be called periodically via cron job or background task.';
