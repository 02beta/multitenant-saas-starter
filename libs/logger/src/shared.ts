export type Fields = Record<string, unknown>;

export type LogLevel = "debug" | "info" | "warn" | "error";

export const SENSITIVE_KEYS = [
  "password",
  "token",
  "authorization",
  "secret",
  "cookie",
  "api_key",
  "apikey",
  "access_token",
  "refresh_token",
];

export function redact(fields: Fields): Fields {
  const out: Fields = {};
  for (const [key, value] of Object.entries(fields)) {
    out[key] = SENSITIVE_KEYS.includes(key.toLowerCase())
      ? "[REDACTED]"
      : value;
  }
  return out;
}
