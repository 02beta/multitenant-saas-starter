const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Retrieve the current user from the API using the access token in localStorage.
 *
 * Returns the user object if authenticated, otherwise null.
 */
export async function getCurrentUserClient(): Promise<any | null> {
  const token = getAccessToken();

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
export async function getCurrentOrganizationClient(): Promise<any | null> {
  const user = await getCurrentUserClient();
  return user?.organization || null;
}

/**
 * Retrieve the memberships of the authenticated user.
 *
 * Returns an array of memberships, or an empty array if none.
 */
export async function getUserMembershipsClient(): Promise<any[]> {
  const user = await getCurrentUserClient();
  return user?.memberships || [];
}

/**
 * Retrieve the members of a given organization.
 *
 * organizationId: The ID of the organization.
 * Returns an array of members, or an empty array if not authenticated or error.
 */
export async function getOrganizationMembersClient(
  organizationId: string
): Promise<any[]> {
  const token = getAccessToken();

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

/**
 * Helper to get the access token from localStorage or cookies.
 *
 * Returns the access token string if present, otherwise null.
 */
function getAccessToken(): string | null {
  // if server side, return null
  if (typeof window === "undefined") {
    return null;
  }
  // attempt to get from localStorage
  const token = window.localStorage.getItem("access_token");
  if (token) {
    return token;
  }
  // fallback: try to get from cookies
  const match = document.cookie.match(/(?:^|; )access_token=([^;]*)/);
  return match ? decodeURIComponent(match[1] || "") : null;
}
