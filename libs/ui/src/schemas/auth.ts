import * as z from "zod";

/**
 * AuthProviderType
 */
export const authProviderTypeSchema = z.enum([
  "supabase",
  "auth0",
  "clerk",
  "custom",
]);

/**
 * TokenPair
 */
export const tokenPairSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string().optional(),
  token_type: z.string().default("bearer"),
  expires_in: z.number().optional(),
  expires_at: z.string().datetime().optional(),
});

/**
 * AuthUser
 */
export const authUserSchema = z.object({
  provider_user_id: z.string(),
  email: z.string().email(),
  provider_type: authProviderTypeSchema,
  provider_metadata: z.record(z.any()).default({}),
  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
});

/**
 * AuthResult
 */
export const authResultSchema = z.object({
  user: authUserSchema,
  tokens: tokenPairSchema,
  session_metadata: z.record(z.any()).default({}),
});

/**
 * SignupRequest
 */
export const signupRequestSchema = z.object({
  first_name: z.string().min(1).max(64),
  last_name: z.string().min(1).max(64),
  organization_name: z.string().max(100).optional().nullable(),
  email: z.string().min(5).max(320).email(),
  password: z.string().min(8).max(128),
});

/**
 * SignupResponse
 */
export const signupResponseSchema = z.object({
  message: z.string(),
  user_id: z.string(),
  organization_id: z.string(),
  requires_email_verification: z.boolean().default(true),
});

/**
 * ForgotPasswordRequest
 */
export const forgotPasswordRequestSchema = z.object({
  email: z.string().min(5).max(320).email(),
});

/**
 * ResetPasswordRequest
 */
export const resetPasswordRequestSchema = z.object({
  password: z.string().min(8).max(128),
  token: z.string(),
});

/**
 * LoginResponseExtended
 */
export const loginResponseExtendedSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string().optional(),
  token_type: z.string(),
  expires_in: z.number().optional(),
  user: z.record(z.any()),
  organization: z.record(z.any()).optional(),
  memberships: z.array(z.record(z.any())).default([]),
});

export type AuthProviderType = z.infer<typeof authProviderTypeSchema>;
export type TokenPair = z.infer<typeof tokenPairSchema>;
export type AuthUser = z.infer<typeof authUserSchema>;
export type AuthResult = z.infer<typeof authResultSchema>;
export type SignupRequest = z.infer<typeof signupRequestSchema>;
export type SignupResponse = z.infer<typeof signupResponseSchema>;
export type ForgotPasswordRequest = z.infer<typeof forgotPasswordRequestSchema>;
export type ResetPasswordRequest = z.infer<typeof resetPasswordRequestSchema>;
export type LoginResponseExtended = z.infer<typeof loginResponseExtendedSchema>;
