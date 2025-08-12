import { config as reactInternalConfig } from "@workspace/eslint-config/react-internal";

/** @type {import("eslint").Linter.Config} */
export default [
  ...reactInternalConfig,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // TypeScript specific rules
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-explicit-any": "warn",
      // "@typescript-eslint/prefer-const": "error",
      "@typescript-eslint/no-var-requires": "error",

      // General rules
      "no-console": "warn",
      "no-debugger": "error",
      "prefer-const": "error",
      "no-var": "error",

      // Import/Export rules
      "import/no-default-export": "off",
      "import/prefer-default-export": "off",
    },
  },
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "*.config.*",
      "*.config.js",
      "*.config.mjs",
    ],
  },
];
