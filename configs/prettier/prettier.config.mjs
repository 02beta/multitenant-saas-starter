import { resolve } from "node:path";

/**
 * Base Prettier configuration for the monorepo.
 *
 * This config references the .prettierignore file located as a sibling to this
 * config file. Note: Prettier CLI should be invoked with --ignore-path if you
 * want to use this ignore file, as Prettier does not read ignorePath from config.
 */
const config = {
  semi: true,
  trailingComma: "es5",
  singleQuote: false,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  bracketSpacing: true,
  arrowParens: "avoid",
  // Informational: path to the ignore file for CLI usage
  ignorePath: resolve(process.cwd(), "configs/prettier-config/.prettierignore"),
};

export default config;
