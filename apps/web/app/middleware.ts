import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Skip public routes
  const publicRoutes = [
    "/login",
    "/signup",
    "/forgot-password",
    "/_next",
    "/favicon.ico",
    "/robots.txt",
    "/sitemap.xml",
  ];
  if (publicRoutes.some(p => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token =
    req.cookies.get("access_token")?.value ||
    req.headers.get("x-access-token") ||
    null;
  // For simplicity in dev, allow reading token from localStorage via client redirect.
  // On server, if no token cookie, redirect to login.
  if (!token && pathname === "/") {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};
