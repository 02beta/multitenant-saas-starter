export const protocol =
  process.env.NODE_ENV === "production" ? "https" : "http";

export const rootDomain = process.env.NEXT_PUBLIC_APP_URL || "localhost:3000";

export const apiUrl =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
