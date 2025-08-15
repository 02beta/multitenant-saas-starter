import { withAxiom } from "next-axiom";

/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@workspace/ui", "@workspace/typescript-sdk"],
  turbopack: {
    resolveAlias: {
      "@/lib": "lib/index.ts",
      "@workspace/ui": "../../libs/ui/src",
      "@workspace/ui/components": "../../libs/ui/src/components",
      "@workspace/ui/components/ui": "../../libs/ui/src/components/ui",
      "@workspace/ui/lib": "../../libs/ui/src/lib",
      "@workspace/ui/styles": "../../libs/ui/src/styles",
      "@workspace/ui/hooks": "../../libs/ui/src/hooks",
      "@workspace/eslint-config": "../../libs/eslint-config",
      "@workspace/typescript-config": "../../libs/typescript-config",
      "@workspace/typescript-sdk": "../../libs/typescript-sdk/src",
    },
  },
};

export default withAxiom(nextConfig);
