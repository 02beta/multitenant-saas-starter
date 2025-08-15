/**
 * CSRF Protection Hook
 * 
 * This hook manages CSRF tokens for API requests.
 * It reads the CSRF token from cookies and includes it in request headers.
 */

import { useEffect, useState } from 'react';

export function useCSRF() {
  const [csrfToken, setCSRFToken] = useState<string | null>(null);

  useEffect(() => {
    // Get CSRF token from cookie
    const getCSRFToken = () => {
      const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/);
      return match ? decodeURIComponent(match[1] || '') : null;
    };

    // Initial token fetch
    const token = getCSRFToken();
    setCSRFToken(token);

    // If no token exists, make a GET request to initialize it
    if (!token) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`, {
        credentials: 'include',
      }).then(() => {
        const newToken = getCSRFToken();
        setCSRFToken(newToken);
      });
    }
  }, []);

  /**
   * Helper function to add CSRF token to fetch headers
   */
  const fetchWithCSRF = async (url: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers);
    
    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken);
    }

    return fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Always include cookies
    });
  };

  return {
    csrfToken,
    fetchWithCSRF,
  };
}

/**
 * Helper function to get CSRF token for use in API client utilities
 */
export function getCSRFToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  
  const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1] || '') : null;
}

/**
 * Helper function to add CSRF headers to request options
 */
export function addCSRFHeader(options: RequestInit = {}): RequestInit {
  const csrfToken = getCSRFToken();
  
  if (!csrfToken) {
    return options;
  }

  const headers = new Headers(options.headers);
  headers.set('X-CSRF-Token', csrfToken);

  return {
    ...options,
    headers,
  };
}