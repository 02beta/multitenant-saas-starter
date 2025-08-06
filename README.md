# Full-Stack Multi-Tenant SaaS Starter

The ultimate modern SaaS boilerplate to get you from idea to production in record time.
Built with a carefully curated tech stack using the latest stable versions, this Turborepo-powered template eliminates months of setup and configuration so you can focus on building features that matter.

## ✨ What Makes This Special

- ⚡ **Lightning Fast Development** — Turborepo monorepo with optimized build pipeline
- 🏢 **Enterprise-Ready Multi-Tenancy** — Complete tenant isolation and management out of the box
- 🔐 **Bulletproof Authentication** — NextAuth.js with multiple providers and security best practices
- 🎨 **Beautiful by Default** — shadcn/ui components with Tailwind CSS v4 for stunning, responsive designs
- 🔒 **Type-Safe Everything** — Full TypeScript frontend with Python SQLModel backend
- 📊 **Real-Time Ready** — Supabase integration for instant data sync and realtime features
- 🚀 **Production Optimized** — Battle-tested patterns for scaling and deployment

## 🛠️ Premium Tech Stack

**Frontend Powerhouse:**

- Next.js v15 App Router — The React framework for production
- Tailwind CSS v4 — Latest utility-first styling
- shadcn/ui — High-quality, accessible components
- NextAuth.js — Secure, flexible authentication

**Backend Excellence:**

- FastAPI — High-performance Python API framework
- SQLModel — Type-safe database operations
- Supabase — PostgreSQL with superpowers

**Developer Experience:**

- Turborepo — Monorepo build system that actually works
- Full TypeScript — End-to-end type safety
- Latest stable versions — Stay current without the headaches

## 🎯 Written For

- ✅ **SaaS Founders** — Skip the boilerplate, start building features
- ✅ **Development Teams** — Production-ready patterns and best practices
- ✅ **Learning Developers** — See how modern full-stack apps are built
- ✅ **Agencies** — Reliable foundation for client projects

Stop wasting time on setup. Start building the future.

⭐ **Star this repo to stay updated with the latest improvements!**

## 📦 Getting Started

This template is for creating a monorepo with shadcn/ui, tailwindcss v4, nextjs v15, fastapi, sqlmodel, supabase, and nextauth for multi-tenant SaaS applications.

### Prerequisites

- [Node.js](https://nodejs.org/) (v18 or higher)
- [pnpm](https://pnpm.io/) package manager
- [Python](https://python.org/) (v3.11 or higher)
- [uv](https://docs.astral.sh/uv/) package manager for Python
- [Supabase CLI](https://supabase.com/docs/guides/cli) (for database operations)

### Installation

```bash
# Install Node.js dependencies
pnpm install

# Install Python dependencies
uv sync
```

### Database Setup

The project includes a powerful CLI for managing Supabase database operations:

```bash
# Initialize the project (creates env files, starts Supabase, sets variables)
python scripts/cli.py db init

# Or using uv directly
uv run cli db init
```

**Available Database Commands:**

```bash
# Initialize project with env files, start Supabase, and set vars
python scripts/cli.py db init

# Create new Supabase project in cloud and link it
python scripts/cli.py db create-new-project

# Ensure all required Supabase env vars are present
python scripts/cli.py db set-vars

# Start Supabase (restarts if already running)
python scripts/cli.py db start

# Stop Supabase
python scripts/cli.py db stop

# Reset Supabase database (stops with reset and restarts)
python scripts/cli.py db reset-db
```

### Development

Then run the following command to launch all apps in development mode:

```bash
turbo dev
```

**Build command (for production):**

```bash
turbo build --filter [name_of_app]
```

**Deploy command:**

```bash
turbo deploy --filter [name_of_app] --env [environment]
```

**Lint command:**

```bash
turbo lint --filter [name_of_app]
```

**Format command:**

```bash
turbo format --filter [name_of_app]
```

**Test command:**

```bash
turbo test --filter [name_of_app]
```
