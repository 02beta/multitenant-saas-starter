"use client";

import { useLogger, LogLevel } from "next-axiom";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

type ErrorPageProps = {
  error: Error & { digest?: string };
};

/**
 * Render the error page and log error details.
 *
 * Arguments:
 * error -- The error object, possibly with a digest property.
 */
export default function ErrorPage({ error }: ErrorPageProps) {
  const pathname = usePathname();
  const log = useLogger({ source: "error.tsx" });
  const status = error.message === "Invalid URL" ? 404 : 500;

  useEffect(() => {
    log.logHttpRequest(
      LogLevel.error,
      error.message,
      {
        host: typeof window !== "undefined" ? window.location.href : "",
        path: pathname,
        statusCode: status,
      },
      {
        error: error.name,
        cause: error.cause,
        stack: error.stack,
        digest: error.digest,
      }
    );
    // Only log once per error
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error, pathname, status, log]);

  return (
    <div className="p-8">
      <span>Oops! An error has occurred:</span>
      <p className="text-red-400 px-8 py-2 text-lg">{error.message}</p>
    </div>
  );
}
