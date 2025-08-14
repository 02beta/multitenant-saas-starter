import { cookies } from "next/headers";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Retrieve the current user from the API using the access token cookie.
 *
 * Returns the user object if authenticated, otherwise null.
 */
export async function getCurrentUser() {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/auth/me/extended`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Retrieve the current organization of the authenticated user.
 *
 * Returns the organization object if available, otherwise null.
 */
export async function getCurrentOrganization() {
  const user = await getCurrentUser();
  return user?.organization || null;
}

/**
 * Retrieve the memberships of the authenticated user.
 *
 * Returns an array of memberships, or an empty array if none.
 */
export async function getUserMemberships() {
  const user = await getCurrentUser();
  return user?.memberships || [];
}

/**
 * Retrieve the members of a given organization.
 *
 * organizationId: The ID of the organization.
 * Returns an array of members, or an empty array if not authenticated or error.
 */
export async function getOrganizationMembers(organizationId: string) {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    return [];
  }

  try {
    const response = await fetch(
      `${API_URL}/memberships?organization_id=${organizationId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      return [];
    }

    return await response.json();
  } catch {
    return [];
  }
}
