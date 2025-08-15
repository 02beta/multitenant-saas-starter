import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware to handle authentication-based redirects.
 *
 * Ensures that only specific static files/resources/images/assets located in
 * the public folder (i.e., any path starting with /public/, /assets/, etc. and
 * ending with an allowed extension) are accessible to unauthenticated users.
 *
 * Retrieves the access token from the HTTP-only cookie set by the FastAPI
 * server's login response. The token is accessed via request.cookies,
 * which is available to Next.js middleware running on the Edge.
 */
export function middleware(request: NextRequest) {
  // Retrieve the access token from the HTTP-only cookie set by FastAPI
  const token = request.cookies.get("access_token")?.value;
  const pathname = request.nextUrl.pathname;

  // Define allowed static file extensions for public assets
  const allowedExtensions = [
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".gif",
    ".webp",
    ".ico",
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
  ];

  // Allow only requests to public assets with allowed extensions
  const isPublicAsset =
    (pathname.startsWith("/assets/") ||
      pathname.startsWith("/images/") ||
      pathname.startsWith("/fonts/") ||
      pathname.startsWith("/public/")) &&
    allowedExtensions.some((ext) => pathname.toLowerCase().endsWith(ext));

  if (isPublicAsset) {
    return NextResponse.next();
  }

  // Check if it's an auth page (login, signup, forgot-password, reset-password)
  const isAuthPage =
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password";

  // Define public pages that don't require authentication
  // Only the root landing page is public by default
  const isPublicPage = pathname === "/";

  // Redirect unauthenticated users to login, except for auth pages and public pages
  if (!token && !isAuthPage && !isPublicPage) {
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
