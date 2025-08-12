import { createClient } from "@axiomhq/js";
import { Fields, LogLevel, redact } from "./shared";

const ENV = process.env.NODE_ENV ?? "development";
const APP = process.env.NEXT_PUBLIC_APP_NAME ?? "node";
const DATASET = process.env.NEXT_PUBLIC_AXIOM_DATASET ?? "logs";

const client = createClient({
  token: process.env.NEXT_PUBLIC_AXIOM_TOKEN ?? "",
});

async function send(level: LogLevel, message: string, fields: Fields) {
  await client.ingest(DATASET, [
    { level, message, app: APP, env: ENV, ...redact(fields) },
  ]);
}

export const logger = {
  debug: (m: string, f: Fields = {}) => send("debug", m, f),
  info: (m: string, f: Fields = {}) => send("info", m, f),
  warn: (m: string, f: Fields = {}) => send("warn", m, f),
  error: (m: string, f: Fields = {}) => send("error", m, f),
  with(additional: Fields) {
    const base = redact(additional);
    return {
      debug: (m: string, f: Fields = {}) => send("debug", m, { ...base, ...f }),
      info: (m: string, f: Fields = {}) => send("info", m, { ...base, ...f }),
      warn: (m: string, f: Fields = {}) => send("warn", m, { ...base, ...f }),
      error: (m: string, f: Fields = {}) => send("error", m, { ...base, ...f }),
    };
  },
};

export type { Fields, LogLevel };
