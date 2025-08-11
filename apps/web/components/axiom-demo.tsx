"use client";

import { useEffect } from "react";
import { log } from "next-axiom";

export function AxiomDemo(): JSX.Element {
  useEffect(() => {
    log.debug("new sign-in challenge", {
      customerId: 32423,
      auth: "session",
    });
  }, []);

  return null;
}
