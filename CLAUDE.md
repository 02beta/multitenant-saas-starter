# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack multi-tenant SaaS starter built as a Turborepo monorepo combining Next.js (TypeScript) frontend with FastAPI (Python) backend. The project uses Supabase for database and authentication, follows Domain-Driven Design principles, and provides enterprise-ready multi-tenancy through organization-based access control.

## Key Commands

### Development

```bash
# Start all services (frontend + backend)
turbo dev

# Start individual apps
pnpm dev --filter web       # Frontend only
pnpm dev --filter api       # Backend only

# Stop development processes
pnpm run dev:kill
# or
uv run cli workspace dev-stop
```

### Database Management

```bash
# Initialize project (creates env files, starts Supabase, sets variables)
uv run cli db init

# Start/restart Supabase
uv run cli db start

# Stop Supabase
uv run cli db stop

# Reset database
uv run cli db reset-db

# Create new cloud Supabase project
uv run cli db create-new-project
```

### Code Quality

```bash
# Linting
turbo lint
turbo lint --fix

# Formatting
turbo format

# Type checking (TypeScript)
turbo typecheck
```

### Release Management

```bash
# Create PR for releases
uv run cli release create-patch-pr
uv run cli release create-minor-pr
uv run cli release create-major-pr

# Create GitHub release
uv run cli release create-github-release

# Version management
uv run cli release sync-versions
```

## Architecture & Structure

### Monorepo Layout

```sh title="Monorepo Layout"
apps/
├── web/          # Next.js v15 App Router frontend
└── api/          # FastAPI backend server

libs/
├── ui/           # shadcn/ui component library (shared)
├── shared/       # TypeScript schemas/types (shared)
├── core/         # Python domain logic (SQLModel)
└── supabase-auth/# Supabase authentication provider

tools/
└── cli/          # Project management CLI tool

infra/
└── supabase/     # Local Supabase configuration
```

### Frontend Architecture (apps/web)

- **Framework**: Next.js v15 with App Router
- **Styling**: Tailwind CSS v4 with shadcn/ui components from `@workspace/ui`
- **State**: React hooks and context
- **Type Safety**: Zod schemas shared via `@workspace/shared`
- **API Client**: Generated from OpenAPI using openapi-zod-client

### Backend Architecture (apps/api)

- **Framework**: FastAPI with async/await patterns
- **Database**: SQLModel (type-safe ORM on SQLAlchemy)
- **Structure**: Domain-driven with route/dependency separation
- **Domains**: auth, users, organizations, memberships
- **Multi-tenancy**: Schema-based isolation (identity, org, public)

### Database Schema Design

- **identity schema**: User authentication and profiles
- **org schema**: Organizations and memberships
- **public schema**: Application-specific data
- All models use UUID primary keys and include audit fields (created_at, updated_at)
- Soft delete support via SoftDeleteMixin

## Development Guidelines

### Python/FastAPI Guidelines

- All routes should be async unless explicitly required
- Use dependencies for validation and auth
- Follow the repository pattern with service layer
- Models inherit from SQLModel with `table=True`
- Always include `__table_args__ = {"schema": "schema_name"}`
- Use Pydantic v2 for request/response validation
- Format with ruff: `uv run ruff format .`

### TypeScript/Next.js Guidelines

- Use App Router patterns (not Pages Router)
- Import UI components from `@workspace/ui`
- Share types via `@workspace/shared`
- Follow existing component patterns in the codebase
- Use server components by default, client components when needed
- Implement proper error boundaries and loading states

### Multi-tenant Considerations

- Always filter by organization_id in queries
- Use row-level security in Supabase
- Validate user membership before granting access
- Keep tenant data isolated at the database level

## Environment Variables

The project uses `.env` files for configuration. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key

Use `uv run cli db init` to automatically set up environment files.

## Testing Strategy

Currently, the project doesn't have comprehensive test coverage. When adding tests:

- **Frontend**: Use Vitest with React Testing Library
- **Backend**: Use pytest with pytest-asyncio
- **E2E**: Consider Playwright for full-stack testing
- Use the local Supabase instance for test databases

## Common Workflows

### Adding a New Domain (Backend)

1. Create directory: `libs/core/src/core/<domain>/`
2. Required files: `__init__.py`, `models.py`, `repository.py`, `services.py`, `exceptions.py`
3. Define SQLModel with proper schema in `__table_args__`
4. Implement repository with CRUD operations
5. Create service layer with business logic
6. Add router in `apps/api/routes/<domain>/`

### Adding UI Components

1. Components should be added to `libs/ui/src/components/`
2. Export from appropriate index file
3. Follow shadcn/ui patterns and conventions
4. Use Tailwind CSS v4 for styling
5. Ensure dark mode support via CSS variables

### Database Migrations

Currently using Supabase migrations. For schema changes:

1. Modify models in `libs/core/`
2. Generate migration with Supabase CLI
3. Test locally with `uv run cli db reset-db`
4. Apply to production via Supabase dashboard

## Important Notes

- The project uses cutting-edge versions (Next.js 15, Tailwind CSS 4)
- Python code follows Domain-Driven Design principles
- All IDs are UUIDs, never use auto-incrementing integers
- Always use absolute imports in Python
- Follow REST conventions for API endpoints
- Maintain type safety across the full stack
