-- ============================================================================
-- DROP ALL EXISTING TABLES IN SCHEMAS
-- ============================================================================
-- Drop tables in reverse order to avoid FK constraints
drop table if exists org.memberships CASCADE;

drop table if exists org.organizations CASCADE;

drop table if exists usr.users CASCADE;

-- Drop schemas
drop schema IF exists usr CASCADE;

drop schema IF exists org CASCADE;

-- Drop any custom functions
drop function IF exists usr.create_user CASCADE;

drop function IF exists usr.update_user CASCADE;

drop function IF exists org.create_organization CASCADE;

drop function IF exists org.update_organization CASCADE;

drop function IF exists org.create_membership CASCADE;

drop function IF exists org.update_membership CASCADE;

-- Drop any custom types
drop type IF exists usr.user_role CASCADE;

drop type IF exists org.membership_role CASCADE;

drop type IF exists org.membership_status CASCADE;

-- Create schemas if they don't exist
create schema IF not exists usr;

create schema IF not exists org;

-- ============================================================================
-- SECTION 1: usr.users TABLE - Simplified with auth user integration
-- ============================================================================
create table if not exists usr.users (
  -- Primary key
  id UUID primary key default gen_random_uuid (),
  -- Basic user fields
  full_name VARCHAR(64) not null,
  email VARCHAR(320) not null unique,
  phone VARCHAR(20),
  -- Additional profile fields requested
  avatar_url VARCHAR(512),
  -- Auth integration fields (CORRECTED REFERENCE)
  auth_user_id UUID not null unique,
  hashed_password VARCHAR(512) not null, -- hashed password stored here
  -- Add foreign key constraint without cross-database reference
  -- We'll create a trigger/function later to ensure this ID exists in auth.users
  -- Permission fields
  is_active BOOLEAN default true not null,
  permissions JSONB,
  is_superuser BOOLEAN default false not null,
  -- Audit fields
  created_at TIMESTAMPTZ not null default NOW(),
  updated_at TIMESTAMPTZ not null default NOW(),
  -- Initial user creation needs to be deferred since we reference the same table
  created_by UUID references usr.users (id) deferrable initially DEFERRED,
  updated_by UUID references usr.users (id) deferrable initially DEFERRED,
  -- Soft delete fields
  deleted_at TIMESTAMPTZ,
  deleted_by UUID references usr.users (id) deferrable initially DEFERRED
);

-- Indexes for usr.users
create index if not exists idx_users_email on usr.users (email)
where
  deleted_at is null;

create index if not exists idx_users_auth_user_id on usr.users (auth_user_id)
where
  deleted_at is null;

create index if not exists idx_users_deleted_at on usr.users (deleted_at);

-- ============================================================================
-- SECTION 2: org.organizations TABLE
-- ============================================================================
create table if not exists org.organizations (
  -- Primary key
  id UUID primary key default gen_random_uuid (),
  -- Organization fields
  name VARCHAR(100) not null,
  -- url friendly slug for subdomain implementations
  slug VARCHAR(50) not null unique,
  -- url to an image to use as an avatar for the org
  avatar_url VARCHAR(512),
  -- flag for active orgs
  is_active BOOLEAN not null default true,
  -- link to owner usr.users record
  owner_id UUID references usr.users (id),
  -- Audit fields
  created_at TIMESTAMPTZ not null default NOW(),
  updated_at TIMESTAMPTZ not null default NOW(),
  created_by UUID not null references usr.users (id),
  updated_by UUID not null references usr.users (id),
  -- Soft delete fields
  deleted_at TIMESTAMPTZ,
  deleted_by UUID references usr.users (id)
);

-- Indexes for org.organizations
create index if not exists idx_organizations_slug on org.organizations (slug)
where
  deleted_at is null;

create index if not exists idx_organizations_avatar_url on org.organizations (avatar_url)
where
  avatar_url is not null
  and deleted_at is null;

create index if not exists idx_organizations_deleted_at on org.organizations (deleted_at);

-- ============================================================================
-- SECTION 3: org.memberships TABLE
-- ============================================================================
create table if not exists org.memberships (
  -- Primary key
  id UUID primary key default gen_random_uuid (),
  -- Membership fields
  organization_id UUID not null references org.organizations (id),
  user_id UUID not null references usr.users (id),
  role INTEGER not null default 2, -- 0=owner, 1=editor, 2=viewer
  status INTEGER not null default 0, -- 0=invited, 1=active
  -- Invitation fields
  invited_by UUID references usr.users (id),
  invited_at TIMESTAMPTZ not null default NOW(),
  accepted_at TIMESTAMPTZ,
  -- Audit fields
  created_at TIMESTAMPTZ not null default NOW(),
  updated_at TIMESTAMPTZ not null default NOW(),
  created_by UUID not null references usr.users (id),
  updated_by UUID not null references usr.users (id),
  -- Soft delete fields
  deleted_at TIMESTAMPTZ,
  deleted_by UUID references usr.users (id),
  -- Ensure a user can only have one active membership per organization
  constraint unique_active_membership unique (organization_id, user_id, deleted_at)
);

-- Indexes for org.memberships
create index if not exists idx_memberships_org_user on org.memberships (organization_id, user_id)
where
  deleted_at is null;

create index if not exists idx_memberships_user_id on org.memberships (user_id)
where
  deleted_at is null;

create index if not exists idx_memberships_status on org.memberships (status)
where
  deleted_at is null;

create index if not exists idx_memberships_deleted_at on org.memberships (deleted_at);

-- ============================================================================
-- SECTION 4: Validation Function for auth.users reference
-- ============================================================================
-- Function to check if auth_user_id exists in auth.users
CREATE OR REPLACE FUNCTION usr.check_auth_user_exists()
RETURNS TRIGGER AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = NEW.auth_user_id) THEN
    RAISE EXCEPTION 'User with ID % does not exist in auth.users', NEW.auth_user_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to validate auth_user_id references a valid auth.users record
CREATE OR REPLACE TRIGGER validate_auth_user_reference
BEFORE INSERT OR UPDATE ON usr.users
FOR EACH ROW
EXECUTE FUNCTION usr.check_auth_user_exists();

-- ============================================================================
-- SECTION 5: First User Creation Helper Function
-- ============================================================================
-- Function to help create the first user (solves chicken-egg problem with created_by/updated_by)
CREATE OR REPLACE FUNCTION usr.create_first_user(
  p_full_name VARCHAR(64),
  p_email VARCHAR(320),
  p_auth_user_id UUID,
  p_is_superuser BOOLEAN DEFAULT TRUE
)
RETURNS UUID AS $$
DECLARE
  v_user_id UUID;
BEGIN
  -- Check if any users exist
  IF EXISTS (SELECT 1 FROM usr.users WHERE deleted_at IS NULL) THEN
    RAISE EXCEPTION 'First user already exists. Use standard user creation.';
  END IF;

  -- Insert first user with self-references for created_by/updated_by
  INSERT INTO usr.users (
    full_name, email, auth_user_id, is_superuser,
    created_by, updated_by
  )
  VALUES (
    p_full_name, p_email, p_auth_user_id, p_is_superuser,
    gen_random_uuid(), gen_random_uuid() -- Temporary IDs that will be updated
  )
  RETURNING id INTO v_user_id;

  -- Update the user to reference itself for created_by/updated_by
  UPDATE usr.users
  SET created_by = v_user_id, updated_by = v_user_id
  WHERE id = v_user_id;

  RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;
