# @workspace/logger

Lightweight, thin wrapper around Axiom logging for consistent, structured logs across apps.

- Common fields: `app`, `env`, `requestId`, `orgId`, `userId`, `traceId`
- Levels: `debug`, `info`, `warn`, `error`
- Redaction of sensitive fields: `password`, `token`, `authorization`, `secret`, `cookie`, etc.
- Transports: `next-axiom` (Next.js) and `@axiomhq/js` (Node)

## Usage (Next.js)

```ts
import { withAxiom, logger } from "@workspace/logger/next";

export const GET = withAxiom(async (req: Request) => {
  const l = logger.with({
    requestId: req.headers.get("x-request-id") ?? undefined,
  });
  l.info("Handling request", { route: "/api" });
  return new Response("ok");
});
```

## Usage (Node)

```ts
import { logger } from "@workspace/logger/node";

await logger.with({ orgId: "org_123" }).info("Job started");
```

## Env

- `NEXT_PUBLIC_APP_NAME` (Next.js)
- `APP_NAME` (Node)
- `AXIOM_TOKEN` (Node)
- `AXIOM_DATASET` (Node) (default: `logs`)
