import { makeApi, Zodios, type ZodiosOptions } from "@zodios/core";
import { z } from "zod";

const LoginRequest = z
  .object({
    email: z.string(),
    password: z.string(),
    organization_id: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const LoginResponse = z
  .object({
    access_token: z.string(),
    refresh_token: z.union([z.string(), z.null()]),
    token_type: z.string(),
    expires_in: z.union([z.number(), z.null()]),
    user: z.object({}).partial().passthrough(),
  })
  .passthrough();
const ValidationError = z
  .object({
    loc: z.array(z.union([z.string(), z.number()])),
    msg: z.string(),
    type: z.string(),
  })
  .passthrough();
const HTTPValidationError = z
  .object({ detail: z.array(ValidationError) })
  .partial()
  .passthrough();
const SignupRequest = z
  .object({
    first_name: z.string().min(1).max(64),
    last_name: z.string().min(1).max(64),
    organization_name: z.union([z.string(), z.null()]).optional(),
    email: z.string().min(5).max(320),
    password: z.string().min(8).max(128),
  })
  .passthrough();
const SignupResponse = z
  .object({
    message: z.string(),
    user_id: z.string(),
    organization_id: z.string(),
    requires_email_verification: z.boolean().optional().default(true),
  })
  .passthrough();
const ForgotPasswordRequest = z
  .object({ email: z.string().min(5).max(320) })
  .passthrough();
const ResetPasswordRequest = z
  .object({ password: z.string().min(8).max(128), token: z.string() })
  .passthrough();
const LoginResponseExtended = z
  .object({
    access_token: z.string(),
    refresh_token: z.union([z.string(), z.null()]),
    token_type: z.string(),
    expires_in: z.union([z.number(), z.null()]),
    user: z.object({}).partial().passthrough(),
    organization: z
      .union([z.object({}).partial().passthrough(), z.null()])
      .optional(),
    memberships: z.array(z.object({}).partial().passthrough()).optional(),
  })
  .passthrough();
const UserCreate = z
  .object({
    email: z.string().min(5).max(320),
    first_name: z.string().min(1).max(64),
    last_name: z.string().min(1).max(64),
  })
  .passthrough();
const UserPublic = z
  .object({
    email: z.string().min(5).max(320),
    first_name: z.string().min(1).max(64),
    last_name: z.string().min(1).max(64),
    id: z.string().uuid(),
    is_active: z.boolean(),
    is_superuser: z.boolean(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.union([z.string(), z.null()]).optional(),
    full_name: z.string(),
  })
  .passthrough();
const UserUpdate = z
  .object({
    email: z.union([z.string(), z.null()]),
    password: z.union([z.string(), z.null()]),
    first_name: z.union([z.string(), z.null()]),
    last_name: z.union([z.string(), z.null()]),
    is_active: z.union([z.boolean(), z.null()]),
    is_superuser: z.union([z.boolean(), z.null()]),
  })
  .partial()
  .passthrough();
const PasswordChangeRequest = z
  .object({ current_password: z.string(), new_password: z.string() })
  .passthrough();
const GeneratePasswordResponse = z
  .object({ password: z.string() })
  .passthrough();
const OrganizationCreate = z
  .object({
    name: z.string().min(1).max(100),
    slug: z.string().min(3).max(50),
    description: z.union([z.string(), z.null()]).optional(),
    website: z.union([z.string(), z.null()]).optional(),
    logo_url: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const OrganizationPublic = z
  .object({
    name: z.string().min(1).max(100),
    slug: z.string().min(3).max(50),
    description: z.union([z.string(), z.null()]).optional(),
    website: z.union([z.string(), z.null()]).optional(),
    logo_url: z.union([z.string(), z.null()]).optional(),
    id: z.string().uuid(),
    is_active: z.boolean(),
    plan_name: z.union([z.string(), z.null()]).optional(),
    max_members: z.number().int(),
    member_count: z.number().int(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const OrganizationUpdate = z
  .object({
    name: z.union([z.string(), z.null()]),
    description: z.union([z.string(), z.null()]),
    website: z.union([z.string(), z.null()]),
    logo_url: z.union([z.string(), z.null()]),
    is_active: z.union([z.boolean(), z.null()]),
  })
  .partial()
  .passthrough();
const MembershipRole = z.union([z.literal(0), z.literal(1), z.literal(2)]);
const MembershipStatus = z.union([z.literal(0), z.literal(1)]);
const MembershipCreate = z
  .object({
    organization_id: z.string().uuid(),
    user_id: z.string().uuid(),
    role: MembershipRole.optional(),
    status: MembershipStatus.optional(),
    invited_by: z.union([z.string(), z.null()]).optional(),
    invited_at: z.union([z.string(), z.null()]).optional(),
    accepted_at: z.union([z.string(), z.null()]).optional(),
  })
  .passthrough();
const MembershipPublic = z
  .object({
    organization_id: z.string().uuid(),
    user_id: z.string().uuid(),
    role: MembershipRole,
    status: MembershipStatus,
    invited_by: z.union([z.string(), z.null()]),
    invited_at: z.union([z.string(), z.null()]),
    accepted_at: z.union([z.string(), z.null()]),
    id: z.string().uuid(),
    created_at: z.string().datetime({ offset: true }),
    updated_at: z.union([z.string(), z.null()]).optional(),
    is_owner: z.boolean(),
    is_active: z.boolean(),
    can_write: z.boolean(),
    can_manage_users: z.boolean(),
  })
  .passthrough();
const MembershipUpdate = z
  .object({
    role: z.union([MembershipRole, z.null()]),
    status: z.union([MembershipStatus, z.null()]),
    accepted_at: z.union([z.string(), z.null()]),
  })
  .partial()
  .passthrough();

export const schemas = {
  LoginRequest,
  LoginResponse,
  ValidationError,
  HTTPValidationError,
  SignupRequest,
  SignupResponse,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  LoginResponseExtended,
  UserCreate,
  UserPublic,
  UserUpdate,
  PasswordChangeRequest,
  GeneratePasswordResponse,
  OrganizationCreate,
  OrganizationPublic,
  OrganizationUpdate,
  MembershipRole,
  MembershipStatus,
  MembershipCreate,
  MembershipPublic,
  MembershipUpdate,
};

const endpoints = makeApi([
  {
    method: "get",
    path: "/",
    alias: "root__get",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "get",
    path: "/health",
    alias: "health_health_get",
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/v1/auth/forgot-password",
    alias: "forgot_password_v1_auth_forgot_password_post",
    description: `Send password reset email.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: z.object({ email: z.string().min(5).max(320) }).passthrough(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/auth/login",
    alias: "login_v1_auth_login_post",
    description: `Login with provider-agnostic authentication.

Sets HTTP-only cookies for access_token and refresh_token.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: LoginRequest,
      },
    ],
    response: LoginResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/auth/logout",
    alias: "logout_v1_auth_logout_post",
    description: `Logout and invalidate session.

Clears authentication cookies.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "get",
    path: "/v1/auth/me",
    alias: "get_current_user_profile_v1_auth_me_get",
    description: `Get current authenticated user profile.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "get",
    path: "/v1/auth/me/extended",
    alias: "get_current_user_extended_v1_auth_me_extended_get",
    description: `Get current user with organization and memberships.`,
    requestFormat: "json",
    response: LoginResponseExtended,
  },
  {
    method: "get",
    path: "/v1/auth/organizations",
    alias: "get_user_organizations_v1_auth_organizations_get",
    description: `Get all organizations for current user.`,
    requestFormat: "json",
    response: z.unknown(),
  },
  {
    method: "post",
    path: "/v1/auth/refresh",
    alias: "refresh_token_v1_auth_refresh_post",
    description: `Refresh access token.

Uses refresh_token from HTTP-only cookie if not provided in body.
Sets new tokens in cookies.`,
    requestFormat: "json",
    response: LoginResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/auth/reset-password",
    alias: "reset_password_v1_auth_reset_password_post",
    description: `Reset password with token.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: ResetPasswordRequest,
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/auth/signup",
    alias: "signup_v1_auth_signup_post",
    description: `Create new user with organization.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: SignupRequest,
      },
    ],
    response: SignupResponse,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/auth/switch-organization",
    alias: "switch_organization_v1_auth_switch_organization_post",
    description: `Switch to a different organization.

Updates the session and sets the organization_id in the session cookie.`,
    requestFormat: "json",
    parameters: [
      {
        name: "organization_id",
        type: "Query",
        schema: z.string().uuid(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/memberships/",
    alias: "create_membership_v1_memberships__post",
    description: `Create a new organization user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: MembershipCreate,
      },
    ],
    response: MembershipPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/memberships/",
    alias: "list_memberships_v1_memberships__get",
    description: `List organization users with pagination.`,
    requestFormat: "json",
    parameters: [
      {
        name: "organization_id",
        type: "Query",
        schema: z.string().uuid(),
      },
      {
        name: "skip",
        type: "Query",
        schema: z.number().int().optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().optional().default(100),
      },
    ],
    response: z.array(MembershipPublic),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/memberships/:membership_id",
    alias: "get_membership_v1_memberships__membership_id__get",
    description: `Get a specific organization user by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "membership_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: MembershipPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/v1/memberships/:membership_id",
    alias: "update_membership_v1_memberships__membership_id__put",
    description: `Update a organization user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: MembershipUpdate,
      },
      {
        name: "membership_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: MembershipPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/v1/memberships/:membership_id",
    alias: "delete_membership_v1_memberships__membership_id__delete",
    description: `Soft delete a organization user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "membership_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/memberships/:membership_id/activate",
    alias: "activate_membership_v1_memberships__membership_id__activate_post",
    description: `Activate a organization user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "membership_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: MembershipPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/memberships/:membership_id/deactivate",
    alias:
      "deactivate_membership_v1_memberships__membership_id__deactivate_post",
    description: `Deactivate a organization user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "membership_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: MembershipPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/memberships/organization/:organization_id/count",
    alias:
      "get_membership_count_v1_memberships_organization__organization_id__count_get",
    description: `Get count of organization users for a specific organization.`,
    requestFormat: "json",
    parameters: [
      {
        name: "organization_id",
        type: "Path",
        schema: z.string().uuid(),
      },
      {
        name: "active_only",
        type: "Query",
        schema: z.boolean().optional().default(true),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/organizations/",
    alias: "create_organization_v1_organizations__post",
    description: `Create a new organization.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrganizationCreate,
      },
    ],
    response: OrganizationPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/organizations/",
    alias: "list_user_organizations_v1_organizations__get",
    description: `List organizations for the current user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "skip",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(1000).optional().default(100),
      },
    ],
    response: z.array(OrganizationPublic),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/organizations/:organization_id",
    alias: "get_organization_v1_organizations__organization_id__get",
    description: `Get a specific organization by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "organization_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: OrganizationPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/v1/organizations/:organization_id",
    alias: "update_organization_v1_organizations__organization_id__put",
    description: `Update a organization.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: OrganizationUpdate,
      },
      {
        name: "organization_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: OrganizationPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/v1/organizations/:organization_id",
    alias: "delete_organization_v1_organizations__organization_id__delete",
    description: `Soft delete a organization.`,
    requestFormat: "json",
    parameters: [
      {
        name: "organization_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/organizations/plan/:plan_name",
    alias: "get_organizations_by_plan_v1_organizations_plan__plan_name__get",
    description: `Get all active organizations on a specific plan.`,
    requestFormat: "json",
    parameters: [
      {
        name: "plan_name",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: z.array(OrganizationPublic),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/organizations/search/by-name",
    alias: "search_organizations_by_name_v1_organizations_search_by_name_get",
    description: `Search organizations by name.`,
    requestFormat: "json",
    parameters: [
      {
        name: "search_term",
        type: "Query",
        schema: z.string().min(1),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(50).optional().default(10),
      },
    ],
    response: z.array(OrganizationPublic),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/organizations/slug/:slug",
    alias: "get_organization_by_slug_v1_organizations_slug__slug__get",
    description: `Get a specific organization by slug.`,
    requestFormat: "json",
    parameters: [
      {
        name: "slug",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: OrganizationPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/",
    alias: "create_user_v1_users__post",
    description: `Create a new user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserCreate,
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/users/",
    alias: "list_users_v1_users__get",
    description: `List users with pagination.`,
    requestFormat: "json",
    parameters: [
      {
        name: "skip",
        type: "Query",
        schema: z.number().int().gte(0).optional().default(0),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(1000).optional().default(100),
      },
      {
        name: "active_only",
        type: "Query",
        schema: z.boolean().optional().default(true),
      },
    ],
    response: z.array(UserPublic),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/users/:user_id",
    alias: "get_user_v1_users__user_id__get",
    description: `Get a user by ID.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "put",
    path: "/v1/users/:user_id",
    alias: "update_user_v1_users__user_id__put",
    description: `Update a user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: UserUpdate,
      },
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "delete",
    path: "/v1/users/:user_id",
    alias: "delete_user_v1_users__user_id__delete",
    description: `Soft delete a user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/:user_id/activate",
    alias: "activate_user_v1_users__user_id__activate_post",
    description: `Activate a user account.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/:user_id/change-password",
    alias: "change_password_v1_users__user_id__change_password_post",
    description: `Change user&#x27;s password.`,
    requestFormat: "json",
    parameters: [
      {
        name: "body",
        type: "Body",
        schema: PasswordChangeRequest,
      },
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/:user_id/deactivate",
    alias: "deactivate_user_v1_users__user_id__deactivate_post",
    description: `Deactivate a user account.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/:user_id/promote",
    alias: "promote_to_superuser_v1_users__user_id__promote_post",
    description: `Promote user to superuser status.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/:user_id/revoke-superuser",
    alias: "revoke_superuser_v1_users__user_id__revoke_superuser_post",
    description: `Revoke superuser status from user.`,
    requestFormat: "json",
    parameters: [
      {
        name: "user_id",
        type: "Path",
        schema: z.string().uuid(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/authenticate",
    alias: "authenticate_user_v1_users_authenticate_post",
    description: `Authenticate a user by email and password.`,
    requestFormat: "json",
    parameters: [
      {
        name: "email",
        type: "Query",
        schema: z.string(),
      },
      {
        name: "password",
        type: "Query",
        schema: z.string(),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/users/count",
    alias: "get_user_count_v1_users_count_get",
    description: `Get total count of users.`,
    requestFormat: "json",
    parameters: [
      {
        name: "active_only",
        type: "Query",
        schema: z.boolean().optional().default(true),
      },
    ],
    response: z.unknown(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/users/email/:email",
    alias: "get_user_by_email_v1_users_email__email__get",
    description: `Get a user by email address.`,
    requestFormat: "json",
    parameters: [
      {
        name: "email",
        type: "Path",
        schema: z.string(),
      },
    ],
    response: UserPublic,
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "post",
    path: "/v1/users/generate-password",
    alias: "generate_secure_password_v1_users_generate_password_post",
    description: `Generate a secure random password.`,
    requestFormat: "json",
    parameters: [
      {
        name: "length",
        type: "Query",
        schema: z.number().int().gte(12).lte(128).optional().default(16),
      },
    ],
    response: z.object({ password: z.string() }).passthrough(),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
  {
    method: "get",
    path: "/v1/users/search/by-name",
    alias: "search_users_by_name_v1_users_search_by_name_get",
    description: `Search users by name or email.`,
    requestFormat: "json",
    parameters: [
      {
        name: "search_term",
        type: "Query",
        schema: z.string().min(1),
      },
      {
        name: "limit",
        type: "Query",
        schema: z.number().int().gte(1).lte(50).optional().default(10),
      },
    ],
    response: z.array(UserPublic),
    errors: [
      {
        status: 422,
        description: `Validation Error`,
        schema: HTTPValidationError,
      },
    ],
  },
]);

export const api = new Zodios(endpoints);

export function createApiClient(baseUrl: string, options?: ZodiosOptions) {
  return new Zodios(baseUrl, endpoints, options);
}
