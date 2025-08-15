import * as z from "zod";

/**
 * OrganizationBase
 */
export const organizationBaseSchema = z.object({
  name: z.string().min(1).max(100),
  slug: z
    .string()
    .min(3)
    .max(50)
    .regex(/^[a-z0-9-]+$/),
  description: z.string().max(500).nullable().optional(),
  website: z.string().max(255).nullable().optional(),
  logo_url: z.string().max(512).nullable().optional(),
});

/**
 * OrganizationCreate
 */
export const organizationCreateSchema = organizationBaseSchema.extend({});

/**
 * OrganizationUpdate
 */
export const organizationUpdateSchema = z.object({
  name: z.string().min(1).max(100).nullable().optional(),
  description: z.string().max(500).nullable().optional(),
  website: z.string().max(255).nullable().optional(),
  logo_url: z.string().max(512).nullable().optional(),
  is_active: z.boolean().nullable().optional(),
});

/**
 * OrganizationPublic
 */
export const organizationPublicSchema = organizationBaseSchema.extend({
  id: z.string().uuid(),
  is_active: z.boolean(),
  plan_name: z.string().nullable().optional(),
  max_members: z.number(),
  member_count: z.number(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime().nullable().optional(),
});

export type OrganizationBase = z.infer<typeof organizationBaseSchema>;
export type OrganizationCreate = z.infer<typeof organizationCreateSchema>;
export type OrganizationUpdate = z.infer<typeof organizationUpdateSchema>;
export type OrganizationPublic = z.infer<typeof organizationPublicSchema>;
