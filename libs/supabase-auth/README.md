# Supabase Authentication Provider

This package provides Supabase authentication integration for the core authentication system.

## Installation

```bash
pip install supabase-auth
```

## Usage

```python
import supabase_auth  # Auto-registers the provider

from core.auth.factory import AuthProviderRegistry
from core.config import settings

# Create provider
provider = AuthProviderRegistry.create_provider("supabase", {
    "api_url": settings.supabase_api_url,
    "anon_key": settings.supabase_public_key,
    "service_role_key": settings.supabase_secret_key,
    "jwt_secret": settings.auth_jwt_secret,
})
```

## Configuration

Set these environment variables:

```bash
AUTH_PROVIDER=supabase
SUPABASE_API_URL=your_supabase_url
SUPABASE_PUBLIC_KEY=your_anon_key
SUPABASE_SECRET_KEY=your_service_role_key
AUTH_JWT_SECRET=your_jwt_secret
```

## Provider Registration

This package automatically registers itself with the core authentication system when imported. The registration happens in the `__init__.py` file and makes the "supabase" provider available to the `AuthProviderRegistry`.
