# @configs/prettier

Shared Prettier configuration for the monorepo.

This package provides a centralized Prettier config that can be reused across all projects in your monorepo, ensuring consistent code formatting.

## Installation

Using [pnpm](https://pnpm.io):

```bash
pnpm add @configs/prettier -w -D # include -w to install in root and -D for dev dependencies
```

## Usage

### prettier.config.mjs

```js
import config from "@configs/prettier/prettier.config.mjs";
export default config;
```

This will automatically use the .prettierignore file located in the same directory as the imported configs.
