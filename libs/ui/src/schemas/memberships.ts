import * as z from "zod";

/**
 * MembershipRole
 * 0 = OWNER, 1 = EDITOR, 2 = VIEWER
 */
export const membershipRoleSchema = z.enum(["OWNER", "EDITOR", "VIEWER"]);

/**
 * MembershipStatus
 * 0 = INVITED, 1 = ACTIVE
 */
export const membershipStatusSchema = z.enum(["INVITED", "ACTIVE"]);

/**
 * MembershipBase
 */
export const membershipBaseSchema = z.object({
  organization_id: z.string().uuid(),
  user_id: z.string().uuid(),
  role: membershipRoleSchema.default("VIEWER"),
  status: membershipStatusSchema.default("INVITED"),
  invited_by: z.string().uuid().nullable().optional(),
  invited_at: z.string().datetime().nullable().optional(),
  accepted_at: z.string().datetime().nullable().optional(),
});

/**
 * MembershipCreate
 */
export const membershipCreateSchema = membershipBaseSchema.extend({
  organization_id: z.string().uuid(),
  user_id: z.string().uuid(),
});

/**
 * MembershipUpdate
 */
export const membershipUpdateSchema = z.object({
  role: membershipRoleSchema.optional(),
  status: membershipStatusSchema.optional(),
  accepted_at: z.string().datetime().nullable().optional(),
});

/**
 * MembershipPublic
 */
export const membershipPublicSchema = membershipBaseSchema.extend({
  id: z.string().uuid(),
  organization_id: z.string().uuid(),
  user_id: z.string().uuid(),
  role: membershipRoleSchema,
  status: membershipStatusSchema,
  invited_by: z.string().uuid().nullable().optional(),
  invited_at: z.string().datetime().nullable().optional(),
  accepted_at: z.string().datetime().nullable().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime().nullable().optional(),
  is_owner: z.boolean(),
  is_active: z.boolean(),
  can_write: z.boolean(),
  can_manage_users: z.boolean(),
});

export type MembershipRole = z.infer<typeof membershipRoleSchema>;
export type MembershipStatus = z.infer<typeof membershipStatusSchema>;
export type MembershipBase = z.infer<typeof membershipBaseSchema>;
export type MembershipCreate = z.infer<typeof membershipCreateSchema>;
export type MembershipUpdate = z.infer<typeof membershipUpdateSchema>;
export type MembershipPublic = z.infer<typeof membershipPublicSchema>;
