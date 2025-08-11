# API

The api package is built on top of FastAPI and depends on the `libs/core` python library which contains all the database models, pydantic schemas for api requests and responses and leverages alembic for database migrations.

## Usage

From the root of the monorepo the api app will launch whenever `turbo dev` command is entered into a terminal from the root of this monorepo project.

Alternatively, you can launch the api app using pnpm scrips by entering:

`pnpm dev --filter api` into a terminal, or by navigating to the root of the api workspace in your terminal and entering: `pnpm dev`

## Structure

The api workspace is structured as follows:

```sh title="API Workspace Structure"
# apps/api/src/api/
├── routes/         # Domain-based routes
│   ├── __init__.py
│   ├── auth/          # Provider-agnostic authentication
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── dependencies.py
│   ├── users/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── dependencies.py
│   ├── organizations/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── dependencies.py
│   └── memberships/
│       ├── __init__.py
│       ├── router.py
│       └── dependencies.py
├── config/
├── utils/
└── main.py
```

The benefit of this structure is that it allows for the api to be more modular and easier to maintain. In the organization of python code in this monorepo, we've been avoiding vendor lock-in by using vendor agnostic code in the `libs/core` workspace. This allows for the api to be more modular and easier to maintain. Supabase auth is the auth provider that is used in this api. The vendor specific code for supabase auth is in the `libs/supabase-auth` workspace which uses protocols defined in the `libs/core` workspace.

## Authentication

The api uses supabase auth for authentication. The vendor specific code for supabase auth is in the `libs/supabase-auth` workspace which uses protocols defined in the `libs/core` workspace.

## Database

The api uses the database defined in the `libs/core` workspace.

## Environment Variables

The api uses environment variables to configure the database and authentication. The environment variables are defined in the `libs/core` workspace.

## Testing

The api uses pytest for testing. The tests are located in the `apps/api/tests` directory.

## Documentation

The api uses pydantic-openapi-helper to generate the openapi schema for the api. The schema is located in the `apps/api/openapi.json` file.

## Logging

The api uses logging to log the requests and responses to the api. The logs are located in the `apps/api/logs` directory.

## Error Handling

The api uses error handling to handle the errors that occur in the api. The error handling is located in the `apps/api/error_handling` directory.
