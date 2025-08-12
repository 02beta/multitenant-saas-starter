// config/environments.ts

/**
 * Get the environment based on the hostname.
 *
 * Example for a tenant named `tenant123`:
 * - https://tenant123.preview.web.02beta.com (preview branch)
 * - https://tenant123.dev.web.02beta.com (staging branch)
 * - https://tenant123.web.02beta.com (production branch)
 *
 * @param hostname - The hostname to get the environment for.
 * @returns The environment based on the hostname.
 */
export const getEnvironment = (hostname: string) => {
  if (hostname.includes(".preview")) {
    return "preview";
  } else if (hostname.includes(".dev")) {
    return "development";
  } else if (hostname.includes(".web")) {
    return "production";
  }
  return "local";
};
