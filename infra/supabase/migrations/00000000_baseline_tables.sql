-- ============================================================================
-- BASELINE TABLE CREATION
-- This file creates all tables with proper structure from scratch
-- Run this before 00000000_baseline_functions_triggers.sql
-- ============================================================================

-- Create schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS org;

-- ============================================================================
-- SECTION 1: identity.users TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS identity.users (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic user fields
    email VARCHAR(320) NOT NULL UNIQUE,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    password VARCHAR(128), -- Nullable for external auth
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,

    -- Provider integration fields
    provider_user_id VARCHAR(255) UNIQUE,
    provider_type VARCHAR(50),
    provider_email VARCHAR(320),
    provider_metadata JSONB DEFAULT '{}',

    -- Profile fields
    avatar_url VARCHAR(512),
    phone VARCHAR(20),
    job_title VARCHAR(100),
    organization_name VARCHAR(100),
    last_login_date TIMESTAMPTZ,
    last_login_location VARCHAR(255),
    timezone VARCHAR(50),
    preferences JSONB DEFAULT '{}',

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES identity.users(id) DEFERRABLE INITIALLY DEFERRED,
    updated_by UUID NOT NULL REFERENCES identity.users(id) DEFERRABLE INITIALLY DEFERRED,

    -- Soft delete fields
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES identity.users(id)
);

-- Indexes for identity.users
CREATE INDEX idx_users_email ON identity.users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_provider_user_id ON identity.users(provider_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_provider_type ON identity.users(provider_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_last_login_date ON identity.users(last_login_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_deleted_at ON identity.users(deleted_at);

-- ============================================================================
-- SECTION 2: org.organizations TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS org.organizations (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Organization fields
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(500),
    website VARCHAR(255),
    logo_url VARCHAR(512),
    avatar_url VARCHAR(512),
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES identity.users(id),
    updated_by UUID NOT NULL REFERENCES identity.users(id),

    -- Soft delete fields
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES identity.users(id)
);

-- Indexes for org.organizations
CREATE INDEX idx_organizations_slug ON org.organizations(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_avatar_url ON org.organizations(avatar_url) WHERE avatar_url IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX idx_organizations_deleted_at ON org.organizations(deleted_at);

-- ============================================================================
-- SECTION 3: org.memberships TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS org.memberships (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Membership fields
    organization_id UUID NOT NULL REFERENCES org.organizations(id),
    user_id UUID NOT NULL REFERENCES identity.users(id),
    role INTEGER NOT NULL DEFAULT 2, -- 0=owner, 1=editor, 2=viewer
    status INTEGER NOT NULL DEFAULT 0, -- 0=invited, 1=active

    -- Invitation fields
    invited_by UUID REFERENCES identity.users(id),
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES identity.users(id),
    updated_by UUID NOT NULL REFERENCES identity.users(id),

    -- Soft delete fields
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES identity.users(id),

    -- Ensure a user can only have one active membership per organization
    CONSTRAINT unique_active_membership UNIQUE (organization_id, user_id, deleted_at)
);

-- Indexes for org.memberships
CREATE INDEX idx_memberships_org_user ON org.memberships(organization_id, user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_memberships_user_id ON org.memberships(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_memberships_status ON org.memberships(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_memberships_deleted_at ON org.memberships(deleted_at);

-- ============================================================================
-- SECTION 4: COMMENTS
-- ============================================================================

-- Comments for identity.users
COMMENT ON TABLE identity.users IS 'Core user table with provider integration and profile fields';
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

-- Comments for org.organizations
COMMENT ON TABLE org.organizations IS 'Organizations for multi-tenant support';
COMMENT ON COLUMN org.organizations.avatar_url IS 'URL to the organization''s avatar image';
COMMENT ON COLUMN org.organizations.logo_url IS 'URL to the organization''s logo image';

-- Comments for org.memberships
COMMENT ON TABLE org.memberships IS 'User memberships in organizations with role-based access';
COMMENT ON COLUMN org.memberships.role IS 'User role: 0=owner (full access), 1=editor (can edit), 2=viewer (read-only)';
COMMENT ON COLUMN org.memberships.status IS 'Membership status: 0=invited (pending), 1=active';

-- ============================================================================
-- END OF BASELINE TABLE CREATION
-- ============================================================================
