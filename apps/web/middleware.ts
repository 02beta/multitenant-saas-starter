import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware to handle authentication-based redirects.
 *
 * Ensures that all files/resources/images/assets located in the public folder
 * (i.e., any path starting with /public/ or /assets/ or direct file access)
 * are accessible to unauthenticated users.
 *
 * Retrieves the access token from the HTTP-only cookie set by the FastAPI
 * server's login response. The token is accessed via request.cookies,
 * which is available to Next.js middleware running on the Edge.
 */
export function middleware(request: NextRequest) {
  // Retrieve the access token from the HTTP-only cookie set by FastAPI
  const token = request.cookies.get("access_token")?.value;
  const pathname = request.nextUrl.pathname;

  // Allow all requests to public assets (e.g., /public/*, /assets/*, /favicon.ico, etc.)
  // Next.js serves static files from /public at the root, so we check for file extensions.
  const isPublicAsset =
    pathname.startsWith("/assets/") ||
    pathname.startsWith("/images/") ||
    pathname.startsWith("/fonts/") ||
    pathname.startsWith("/public/") ||
    /\.[a-zA-Z0-9]+$/.test(pathname); // matches file extensions like .png, .jpg, .svg, .css, etc.

  if (isPublicAsset) {
    return NextResponse.next();
  }

  // Check if it's an auth page (login, signup, forgot-password, reset-password)
  const isAuthPage =
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password";

  // Don't redirect if already on the target page
  if (!token && !isAuthPage && pathname !== "/") {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Redirect authenticated users away from auth pages to dashboard
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
