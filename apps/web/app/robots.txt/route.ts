export function GET() {
  const body = `User-agent: *
Allow: /
Sitemap: ${process.env.NEXT_PUBLIC_WEB_BASE_URL || "http://localhost:3000"}/sitemap.xml
`;
  return new Response(body, {
    headers: { "Content-Type": "text/plain" },
  });
}
