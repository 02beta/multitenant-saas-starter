import { apiUrl } from "./constants";
import {} from "@workspace/shared";
const API_URL = apiUrl;

/**
 * Retrieve the current user from the API using the access token from HTTP-only cookies.
 * Client-side fetches will automatically include cookies with credentials: 'include'.
 *
 * Returns the user object if authenticated, otherwise null.
 */
export async function getCurrentUserClient(): Promise<any | null> {
  try {
    const response = await fetch(`${API_URL}/auth/me/extended`, {
      credentials: 'include', // Include HTTP-only cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Token might be expired, try to refresh
      if (response.status === 401) {
        const refreshed = await refreshTokenClient();
        if (refreshed) {
          // Retry the request after refresh
          const retryResponse = await fetch(`${API_URL}/auth/me/extended`, {
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
          });
          if (retryResponse.ok) {
            return await retryResponse.json();
          }
        }
      }
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
  try {
    const response = await fetch(
      `${API_URL}/memberships?organization_id=${organizationId}`,
      {
        credentials: 'include', // Include HTTP-only cookies
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      // Token might be expired, try to refresh
      if (response.status === 401) {
        const refreshed = await refreshTokenClient();
        if (refreshed) {
          // Retry the request after refresh
          const retryResponse = await fetch(
            `${API_URL}/memberships?organization_id=${organizationId}`,
            {
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json',
              },
            }
          );
          if (retryResponse.ok) {
            return await retryResponse.json();
          }
        }
      }
      return [];
    }

    return await response.json();
  } catch {
    return [];
  }
}

/**
 * Refresh the authentication token using the refresh token cookie.
 * Returns true if refresh was successful, false otherwise.
 */
export async function refreshTokenClient(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include', // Include HTTP-only cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Logout the current user by calling the logout endpoint.
 * This will invalidate the session and clear cookies.
 */
export async function logoutClient(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include', // Include HTTP-only cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      // Clear any client-side state if needed
      window.location.href = '/login';
      return true;
    }
    return false;
  } catch {
    return false;
  }
}
