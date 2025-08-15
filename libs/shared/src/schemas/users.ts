import * as z from "zod";

/**
 * UserBase
 */
export const userBaseSchema = z.object({
  email: z
    .string()
    .min(5)
    .max(320)
    .regex(/^[^@]+@[^@]+\.[^@]+$/),
  first_name: z.string().min(1).max(64),
  last_name: z.string().min(1).max(64),
});

/**
 * UserCreate
 */
export const userCreateSchema = userBaseSchema.extend({});

/**
 * UserUpdate
 */
export const userUpdateSchema = z.object({
  email: z
    .string()
    .min(5)
    .max(320)
    .regex(/^[^@]+@[^@]+\.[^@]+$/)
    .nullable()
    .optional(),
  password: z.string().min(8).max(128).nullable().optional(),
  first_name: z.string().min(1).max(64).nullable().optional(),
  last_name: z.string().min(1).max(64).nullable().optional(),
  is_active: z.boolean().nullable().optional(),
  is_superuser: z.boolean().nullable().optional(),
});

/**
 * UserPublic
 */
export const userPublicSchema = userBaseSchema.extend({
  id: z.string().uuid(),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime().nullable().optional(),
});

export type UserBase = z.infer<typeof userBaseSchema>;
export type UserCreate = z.infer<typeof userCreateSchema>;
export type UserUpdate = z.infer<typeof userUpdateSchema>;
export type UserPublic = z.infer<typeof userPublicSchema>;
