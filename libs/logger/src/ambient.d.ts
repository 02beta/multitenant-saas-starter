declare module "next-axiom" {
  export interface LogMethods {
    debug(message: string, ...args: unknown[]): void;
    info(message: string, ...args: unknown[]): void;
    warn(message: string, ...args: unknown[]): void;
    error(message: string, ...args: unknown[]): void;
    [level: string]: ((message: string, ...args: unknown[]) => void) | unknown;
  }

  export interface LogWith {
    with(fields: Record<string, unknown>): LogMethods;
    debug(message: string, ...args: unknown[]): void;
    info(message: string, ...args: unknown[]): void;
    warn(message: string, ...args: unknown[]): void;
    error(message: string, ...args: unknown[]): void;
    [level: string]: ((message: string, ...args: unknown[]) => void) | unknown;
  }

  export const log: LogWith;
  export function withAxiom(handler: (...args: any[]) => any): any;
}

declare module "@axiomhq/js" {
  export interface AxiomClientOptions {
    token: string;
    [key: string]: unknown;
  }

  export interface AxiomClient {
    ingest(dataset: string, events: Record<string, unknown>[]): Promise<void>;
    // Add other methods as needed
  }

  export function createClient(options: AxiomClientOptions): AxiomClient;
}
