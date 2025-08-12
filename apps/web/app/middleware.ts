import { type NextRequest, NextResponse } from "next/server";
import { rootDomain } from "@/lib/utils";

// Extracts the subdomain from the request
function extractSubdomain(request: NextRequest): string | null {
  const url = request.url;
  const host = request.headers.get("host") || "";
  const hostname = host.split(":")[0] || null;

  // Local development environment
  if (url.includes("localhost") || url.includes("127.0.0.1")) {
    // Try to extract subdomain from the full URL
    const fullUrlMatch = url.match(/http:\/\/([^.]+)\.localhost/);
    if (fullUrlMatch && fullUrlMatch[1]) {
      return fullUrlMatch[1];
    }

    // Fallback to host header approach
    if (hostname && hostname.includes(".localhost")) {
      return hostname.split(".")[0] || null;
    }

    return null;
  }

  // Production environment
  const rootDomainFormatted = rootDomain.split(":")[0];

  // Handle preview deployment URLs (tenant---branch-name.vercel.app)
  if (
    hostname &&
    hostname.includes("---") &&
    hostname.endsWith(".vercel.app")
  ) {
    const parts = hostname.split("---");
    return parts.length > 0 ? parts[0] || null : null;
  }

  // Regular subdomain detection
  const isSubdomain =
    hostname !== rootDomainFormatted &&
    hostname !== `www.${rootDomainFormatted}` &&
    hostname &&
    hostname.endsWith(`.${rootDomainFormatted}`);

  return isSubdomain ? hostname.replace(`.${rootDomainFormatted}`, "") : null;
}

// Middleware to handle requests
export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const requestId =
    req.headers.get("x-request-id") ?? globalThis.crypto.randomUUID();

  const setHeaders = (response: NextResponse) => {
    response.headers.set("x-request-id", requestId);
    response.headers.set("X-Request-ID", requestId);
    return response;
  };

  // Ensure the forwarded request contains the header
  const forwardedHeaders = new Headers(req.headers);
  forwardedHeaders.set("x-request-id", requestId);

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
    return setHeaders(
      NextResponse.next({ request: { headers: forwardedHeaders } })
    );
  }

  const token =
    req.cookies.get("access_token")?.value ||
    req.headers.get("x-access-token") ||
    null;

  if (!token && pathname === "/") {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    const res = NextResponse.redirect(url);
    return setHeaders(res);
  }

  return setHeaders(
    NextResponse.next({ request: { headers: forwardedHeaders } })
  );
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};
