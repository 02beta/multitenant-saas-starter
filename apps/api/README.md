# API

The api package is built on top of FastAPI and depends on the `libs/core` python library which contains all the database models, pydantic schemas for api requests and responses and leverages alembic for database migrations.

## Usage

From the root of the monorepo the api app will launch whenever `turbo dev` command is entered into a terminal from the root of this monorepo project.

Alternatively, you can launch the api app using pnpm scrips by entering:

`pnpm dev --filter api` into a terminal, or by navigating to the root of the api workspace in your terminal and entering: `pnpm dev`
