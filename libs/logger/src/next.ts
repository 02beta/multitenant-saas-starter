import { log, withAxiom } from "next-axiom";
import { Fields, LogLevel, redact } from "./shared";

const ENV = process.env.NODE_ENV ?? "development";
const APP = process.env.NEXT_PUBLIC_APP_NAME ?? "web";

const base =
  (level: LogLevel) =>
  (message: string, fields: Fields = {}) => {
    log.with({ app: APP, env: ENV, ...redact(fields) })[level](message);
  };

export const logger = {
  debug: base("debug"),
  info: base("info"),
  warn: base("warn"),
  error: base("error"),
  with(additional: Fields) {
    const withLogger = log.with({ app: APP, env: ENV, ...redact(additional) });
    return {
      debug: (m: string, f: Fields = {}) => withLogger.debug(m, redact(f)),
      info: (m: string, f: Fields = {}) => withLogger.info(m, redact(f)),
      warn: (m: string, f: Fields = {}) => withLogger.warn(m, redact(f)),
      error: (m: string, f: Fields = {}) => withLogger.error(m, redact(f)),
    };
  },
};

export { withAxiom };
export type { Fields, LogLevel };
