-- Migration: Audit Field Triggers
-- This migration creates triggers to automatically populate audit fields
-- Date: 2025-01-15

-- ============================================================================
-- PART 1: Helper function to get current user ID from auth context
-- ============================================================================

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

-- ============================================================================
-- PART 2: Trigger function for updating audit fields
-- ============================================================================

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

-- ============================================================================
-- PART 3: Trigger function for soft delete
-- ============================================================================

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

-- ============================================================================
-- PART 4: Trigger function for insert (sets created_by and updated_by)
-- ============================================================================

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

-- ============================================================================
-- PART 5: Special trigger for identity.users table (self-reference on create)
-- ============================================================================

CREATE OR REPLACE FUNCTION identity.set_user_self_audit_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- For new user records, set audit fields to self-reference
    IF NEW.created_by IS NULL OR NEW.created_by = gen_random_uuid() THEN
        NEW.created_by = NEW.id;
    END IF;

    IF NEW.updated_by IS NULL OR NEW.updated_by = gen_random_uuid() THEN
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
-- PART 6: Apply triggers to identity.users table
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
-- PART 7: Apply triggers to org.organizations table
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
-- PART 8: Apply triggers to org.memberships table
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
-- PART 9: Helper function to manually set audit fields (for migrations/scripts)
-- ============================================================================

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
-- PART 10: Add comments for documentation
-- ============================================================================

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

COMMENT ON FUNCTION identity.set_audit_fields_for_user(TEXT, TEXT, UUID, UUID, TEXT) IS
'Manual function to set audit fields for a specific user and record (useful for migrations)';

-- Migration complete message
DO $$
BEGIN
    RAISE NOTICE 'Audit field triggers migration completed successfully';
    RAISE NOTICE 'All tables with audit fields will now automatically track created_by, updated_by, and deleted_by';
END $$;
