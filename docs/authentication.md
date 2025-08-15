# Authentication System Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Current Implementation: Supabase](#current-implementation-supabase)
4. [Authentication Flows](#authentication-flows)
5. [Database Schema](#database-schema)
6. [Frontend Integration](#frontend-integration)
7. [API Endpoints](#api-endpoints)
8. [Creating Custom Auth Providers](#creating-custom-auth-providers)
9. [Example: Clerk Integration](#example-clerk-integration)
10. [Example: Custom Auth System](#example-custom-auth-system)
11. [Suggested Improvements](#suggested-improvements)

## Overview

The multitenant-saas-starter implements a **provider-agnostic authentication system** that abstracts authentication providers behind a common protocol. This design enables seamless switching between different authentication providers (Supabase, Auth0, Clerk, custom implementations) without modifying core application logic.

### Key Features

- **Provider Abstraction**: Clean separation between authentication logic and provider implementations
- **Multi-tenancy Support**: Organization-based access control with role-based permissions
- **Session Management**: Secure token handling with HTTP-only cookies
- **Type Safety**: Full TypeScript and Pydantic validation throughout
- **Extensibility**: Easy addition of new authentication providers

## Architecture

### System Components

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        UI[UI Components]
        MW[Middleware]
        AC[Auth Client]
    end

    subgraph "API Layer (FastAPI)"
        AR[Auth Routes]
        AD[Auth Dependencies]
        AS[Auth Service]
    end

    subgraph "Core Library"
        AP[AuthProvider Protocol]
        APR[AuthProvider Registry]
        AM[Auth Models]
    end

    subgraph "Provider Implementations"
        SP[Supabase Provider]
        CP[Clerk Provider]
        CSP[Custom Provider]
    end

    subgraph "Database"
        UT[Users Table]
        AUT[Auth Users Table]
        ST[Sessions Table]
        OT[Organizations Table]
        MT[Memberships Table]
    end

    UI --> MW
    MW --> AC
    AC --> AR
    AR --> AD
    AD --> AS
    AS --> APR
    APR --> AP
    SP -.-> AP
    CP -.-> AP
    CSP -.-> AP
    AS --> AM
    AM --> UT
    AM --> AUT
    AM --> ST
    AM --> OT
    AM --> MT
```

### Provider Protocol

The system defines an `AuthProvider` protocol that all authentication providers must implement:

```python
from typing import Protocol, Dict, Any, Optional
from core.domains.auth.schemas import AuthResult, AuthUser, TokenPair

@runtime_checkable
class AuthProvider(Protocol):
    """Protocol defining the interface for authentication providers."""

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate user with credentials."""
        ...

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token."""
        ...

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh authentication tokens."""
        ...

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create a new user."""
        ...

    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Retrieve user by provider ID."""
        ...

    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Retrieve user by email."""
        ...

    async def update_user(
        self, user_id: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Update user information."""
        ...

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        ...

    async def logout(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """Logout user and invalidate session."""
        ...

    async def send_password_reset(self, email: str) -> bool:
        """Send password reset email."""
        ...

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token."""
        ...
```

### Provider Registry

The `AuthProviderRegistry` manages provider registration and instantiation:

```python
class AuthProviderRegistry:
    """Registry for authentication providers."""

    _providers: Dict[str, Callable[..., AuthProvider]] = {}

    @classmethod
    def register_provider(
        cls, name: str, provider_factory: Callable[..., AuthProvider]
    ) -> None:
        """Register a new authentication provider."""
        cls._providers[name] = provider_factory

    @classmethod
    def create_provider(
        cls, provider_name: str, config: Dict[str, Any]
    ) -> AuthProvider:
        """Create an instance of the specified provider."""
        if provider_name not in cls._providers:
            return AuthProviderStub()  # Fallback for unregistered providers
        return cls._providers[provider_name](config)
```

## Current Implementation: Supabase

### Configuration

The Supabase provider requires the following environment variables:

```env
# Authentication Provider Selection
AUTH_PROVIDER=supabase

# Supabase Configuration
SUPABASE_API_URL=http://localhost:54321
SUPABASE_PUBLIC_KEY=your-anon-key
SUPABASE_SECRET_KEY=your-service-role-key
AUTH_JWT_SECRET=your-jwt-secret
```

### Provider Implementation

Located at `libs/supabase-auth/src/supabase_auth/provider.py`:

```python
class SupabaseAuthProvider(AuthProvider):
    """Supabase implementation of AuthProvider protocol."""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        # User-facing client with anon key
        self.client = create_client(
            config.supabase_api_url,
            config.supabase_public_key
        )
        # Admin client with service role key
        self.admin_client = create_client(
            config.supabase_api_url,
            config.supabase_secret_key
        )

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate with Supabase."""
        response = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        return AuthResult(
            user=self._map_supabase_user(response.user),
            tokens=TokenPair(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                expires_at=datetime.fromtimestamp(response.session.expires_at)
            )
        )
```

### Auto-Registration

The provider self-registers when the package is imported:

```python
# libs/supabase-auth/src/supabase_auth/__init__.py
from core.domains.auth.factory import AuthProviderRegistry
from .provider import SupabaseAuthProvider
from .config import SupabaseConfig

def create_supabase_provider(config: dict) -> SupabaseAuthProvider:
    supabase_config = SupabaseConfig(**config)
    return SupabaseAuthProvider(supabase_config)

# Auto-register on import
AuthProviderRegistry.register_provider("supabase", create_supabase_provider)
```

## Authentication Flows

### User Registration Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant AS as AuthService
    participant P as Provider
    participant DB as Database

    U->>F: Submit registration form
    F->>API: POST /auth/signup
    API->>AS: create_user_with_organization()
    AS->>P: create_user(email, password)
    P-->>AS: AuthUser
    AS->>DB: Create local User record
    AS->>DB: Create Organization
    AS->>DB: Create Membership (OWNER)
    AS->>DB: Create AuthUser link
    AS->>DB: Create AuthSession
    AS-->>API: SignupResponse
    API->>API: Set HTTP-only cookies
    API-->>F: User data + tokens
    F->>F: Store tokens in localStorage
    F->>U: Redirect to dashboard
```

### Login Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant AS as AuthService
    participant P as Provider
    participant DB as Database

    U->>F: Submit login form
    F->>API: POST /auth/login
    API->>AS: authenticate_user()
    AS->>P: authenticate(email, password)
    P-->>AS: AuthResult
    AS->>DB: Sync user data
    AS->>DB: Validate org membership
    AS->>DB: Create/update session
    AS-->>API: AuthResult
    API->>API: Set HTTP-only cookies
    API-->>F: User data + tokens
    F->>F: Store tokens
    F->>U: Redirect to dashboard
```

### Token Validation Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant MW as Middleware
    participant API as FastAPI
    participant AS as AuthService
    participant P as Provider
    participant DB as Database

    F->>MW: Request with token
    MW->>MW: Extract token from cookie
    MW->>API: Forward request + token
    API->>AS: validate_session(token)
    AS->>DB: Check local session
    AS->>P: validate_token(token)
    P-->>AS: Token valid/invalid
    AS->>DB: Update session status
    AS-->>API: Session data
    API-->>F: Protected resource
```

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    Users ||--o{ AuthUsers : "has"
    Users ||--o{ Memberships : "has"
    Users ||--o{ AuthSessions : "has"
    Organizations ||--o{ Memberships : "contains"
    Organizations ||--o{ AuthSessions : "context"
    AuthUsers ||--o{ AuthSessions : "creates"

    Users {
        uuid id PK
        string email UK
        string first_name
        string last_name
        bool is_active
        bool is_superuser
        datetime created_at
        datetime updated_at
    }

    AuthUsers {
        uuid id PK
        uuid local_user_id FK
        string provider_type
        string provider_user_id
        string provider_email
        json provider_metadata
        datetime created_at
        datetime updated_at
    }

    AuthSessions {
        uuid id PK
        uuid local_user_id FK
        uuid auth_user_id FK
        uuid organization_id FK
        string access_token
        string refresh_token
        datetime expires_at
        bool is_active
        datetime created_at
        datetime updated_at
    }

    Organizations {
        uuid id PK
        string name
        string slug UK
        json settings
        datetime created_at
        datetime updated_at
    }

    Memberships {
        uuid id PK
        uuid organization_id FK
        uuid user_id FK
        string role
        string status
        datetime created_at
        datetime updated_at
    }
```

### Schema Definitions

```sql
-- identity schema: Authentication and user data
CREATE SCHEMA IF NOT EXISTS identity;

-- org schema: Multi-tenant organization data
CREATE SCHEMA IF NOT EXISTS org;

-- Users table (identity schema)
CREATE TABLE identity.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Auth Users linking table (identity schema)
CREATE TABLE identity.auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    local_user_id UUID REFERENCES identity.users(id),
    provider_type VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(320) NOT NULL,
    provider_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    UNIQUE(provider_type, provider_user_id)
);

-- Auth Sessions table (identity schema)
CREATE TABLE identity.auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    local_user_id UUID REFERENCES identity.users(id),
    auth_user_id UUID REFERENCES identity.auth_users(id),
    organization_id UUID REFERENCES org.organizations(id),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Organizations table (org schema)
CREATE TABLE org.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Memberships table (org schema)
CREATE TABLE org.memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES org.organizations(id),
    user_id UUID REFERENCES identity.users(id),
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    UNIQUE(organization_id, user_id)
);
```

## Frontend Integration

### Middleware Configuration

The Next.js middleware handles route protection:

```typescript
// apps/web/middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  const pathname = request.nextUrl.pathname

  // Public asset bypass
  const isPublicAsset = /\.[a-zA-Z0-9]+$/.test(pathname)
  if (isPublicAsset) return NextResponse.next()

  // Auth page detection
  const isAuthPage = [
    '/login',
    '/signup',
    '/forgot-password',
    '/reset-password'
  ].includes(pathname)

  // Redirect unauthenticated users to login
  if (!token && !isAuthPage && pathname !== '/') {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Redirect authenticated users away from auth pages
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}
```

### Client-Side Authentication

```typescript
// apps/web/lib/auth.client.ts
function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null

  // Primary: localStorage
  const token = window.localStorage.getItem('access_token')
  if (token) return token

  // Fallback: cookies
  const match = document.cookie.match(/(?:^|; )access_token=([^;]*)/)
  return match ? decodeURIComponent(match[1] || '') : null
}

export async function getCurrentUserClient(): Promise<any | null> {
  const token = getAccessToken()
  if (!token) return null

  const response = await fetch(`${API_URL}/auth/me/extended`, {
    headers: { Authorization: `Bearer ${token}` }
  })

  return response.ok ? await response.json() : null
}
```

### Server-Side Authentication

```typescript
// apps/web/lib/auth.server.ts
import { cookies } from 'next/headers'

export async function getCurrentUserServer(): Promise<any | null> {
  const cookieStore = cookies()
  const token = cookieStore.get('access_token')?.value

  if (!token) return null

  const response = await fetch(`${API_URL}/auth/me/extended`, {
    headers: { Authorization: `Bearer ${token}` }
  })

  return response.ok ? await response.json() : null
}
```

## API Endpoints

### Authentication Routes

| Endpoint                    | Method | Description            | Request Body                                                   | Response                 |
| --------------------------- | ------ | ---------------------- | -------------------------------------------------------------- | ------------------------ |
| `/auth/login`               | POST   | User authentication    | `{email, password, organization_id?}`                          | User data + tokens       |
| `/auth/logout`              | POST   | Session invalidation   | -                                                              | Success status           |
| `/auth/refresh`             | POST   | Token refresh          | `{refresh_token}`                                              | New tokens               |
| `/auth/me`                  | GET    | Current user           | -                                                              | User profile             |
| `/auth/me/extended`         | GET    | User with org data     | -                                                              | User + org + memberships |
| `/auth/signup`              | POST   | User registration      | `{email, password, first_name, last_name, organization_name?}` | User data + tokens       |
| `/auth/forgot-password`     | POST   | Password reset request | `{email}`                                                      | Success status           |
| `/auth/reset-password`      | POST   | Password reset         | `{token, new_password}`                                        | Success status           |
| `/auth/organizations`       | GET    | User's organizations   | -                                                              | Organization list        |
| `/auth/switch-organization` | POST   | Change org context     | `{organization_id}`                                            | Updated session          |

### Example API Calls

```typescript
// Login
const response = await fetch(`${API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
  credentials: 'include' // Important for cookies
})

// Get current user with organization
const response = await fetch(`${API_URL}/auth/me/extended`, {
  headers: { Authorization: `Bearer ${token}` }
})

// Switch organization
const response = await fetch(`${API_URL}/auth/switch-organization`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  },
  body: JSON.stringify({ organization_id })
})
```

## Creating Custom Auth Providers

### Step 1: Create Provider Package

Create a new package in `libs/` directory:

```bash
mkdir -p libs/custom-auth/src/custom_auth
```

### Step 2: Define Configuration

```python
# libs/custom-auth/src/custom_auth/config.py
from pydantic import BaseModel, Field

class CustomAuthConfig(BaseModel):
    """Configuration for custom auth provider."""
    api_url: str = Field(..., description="Custom auth API URL")
    api_key: str = Field(..., description="API key for authentication")
    api_secret: str = Field(..., description="API secret")
    jwt_algorithm: str = Field(default="HS256")
    token_expiry: int = Field(default=3600, description="Token expiry in seconds")
```

### Step 3: Implement Provider

```python
# libs/custom-auth/src/custom_auth/provider.py
import hashlib
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from core.domains.auth.protocols import AuthProvider
from core.domains.auth.schemas import AuthResult, AuthUser, TokenPair
from .config import CustomAuthConfig

class CustomAuthProvider(AuthProvider):
    """Custom authentication provider implementation."""

    def __init__(self, config: CustomAuthConfig):
        self.config = config
        self.users_db: Dict[str, Dict[str, Any]] = {}  # In-memory user store
        self.sessions: Dict[str, Dict[str, Any]] = {}  # In-memory sessions

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate user with custom logic."""
        # Hash password for comparison
        password_hash = self._hash_password(password)

        # Find user in database
        user = self.users_db.get(email)
        if not user or user['password_hash'] != password_hash:
            raise InvalidCredentialsError("Invalid email or password")

        # Generate tokens
        access_token = self._generate_token(user['id'], 'access')
        refresh_token = self._generate_token(user['id'], 'refresh')
        expires_at = datetime.utcnow() + timedelta(seconds=self.config.token_expiry)

        # Store session
        self.sessions[access_token] = {
            'user_id': user['id'],
            'email': email,
            'expires_at': expires_at
        }

        return AuthResult(
            user=AuthUser(
                provider_user_id=user['id'],
                email=email,
                provider_type="custom",
                provider_metadata={'custom_field': user.get('custom_field')}
            ),
            tokens=TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
        )

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate access token."""
        try:
            payload = jwt.decode(
                token,
                self.config.api_secret,
                algorithms=[self.config.jwt_algorithm]
            )

            # Check if session exists and is valid
            session = self.sessions.get(token)
            if not session or session['expires_at'] < datetime.utcnow():
                raise InvalidTokenError("Token expired or invalid")

            return {
                'user_id': payload['user_id'],
                'email': session['email'],
                'type': payload['type']
            }
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create a new user."""
        if email in self.users_db:
            raise UserAlreadyExistsError(f"User {email} already exists")

        user_id = secrets.token_urlsafe(16)
        password_hash = self._hash_password(password)

        self.users_db[email] = {
            'id': user_id,
            'email': email,
            'password_hash': password_hash,
            **user_data
        }

        return AuthUser(
            provider_user_id=user_id,
            email=email,
            provider_type="custom",
            provider_metadata=user_data
        )

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(
            f"{password}{self.config.api_secret}".encode()
        ).hexdigest()

    def _generate_token(self, user_id: str, token_type: str) -> str:
        """Generate JWT token."""
        payload = {
            'user_id': user_id,
            'type': token_type,
            'exp': datetime.utcnow() + timedelta(seconds=self.config.token_expiry)
        }
        return jwt.encode(
            payload,
            self.config.api_secret,
            algorithm=self.config.jwt_algorithm
        )

    # Implement remaining protocol methods...
```

### Step 4: Register Provider

```python
# libs/custom-auth/src/custom_auth/__init__.py
from core.domains.auth.factory import AuthProviderRegistry
from .provider import CustomAuthProvider
from .config import CustomAuthConfig

def create_custom_provider(config: dict) -> CustomAuthProvider:
    custom_config = CustomAuthConfig(**config)
    return CustomAuthProvider(custom_config)

# Auto-register when imported
AuthProviderRegistry.register_provider("custom", create_custom_provider)
```

### Step 5: Update Configuration

```python
# apps/api/config/settings.py
class Settings(BaseSettings):
    # Change provider
    auth_provider: str = Field(default="custom")

    # Add custom provider settings
    custom_auth_api_url: str = Field(default="")
    custom_auth_api_key: str = Field(default="")
    custom_auth_api_secret: str = Field(default="")
```

### Step 6: Import Provider

```python
# apps/api/routes/auth/dependencies.py
async def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    # Import to trigger registration
    if settings.auth_provider == "custom":
        import custom_auth  # noqa: F401

    # Rest of the code remains the same...
```

## Example: Clerk Integration

### Step 1: Create Clerk Provider Package

```bash
mkdir -p libs/clerk-auth/src/clerk_auth
```

### Step 2: Install Clerk SDK

```bash
cd libs/clerk-auth
uv add clerk-backend-api
```

### Step 3: Implement Clerk Provider

```python
# libs/clerk-auth/src/clerk_auth/provider.py
from typing import Dict, Any, Optional
from datetime import datetime
from clerk_backend_api import Clerk
from clerk_backend_api.models import User as ClerkUser
from core.domains.auth.protocols import AuthProvider
from core.domains.auth.schemas import AuthResult, AuthUser, TokenPair
from core.domains.auth.exceptions import InvalidCredentialsError
from .config import ClerkConfig

class ClerkAuthProvider(AuthProvider):
    """Clerk authentication provider implementation."""

    def __init__(self, config: ClerkConfig):
        self.config = config
        self.clerk = Clerk(bearer_auth=config.secret_key)

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate with Clerk."""
        try:
            # Create a session with email/password
            session = self.clerk.sessions.create_session(
                identifier=email,
                password=password
            )

            # Get user details
            user = self.clerk.users.get(user_id=session.user_id)

            return AuthResult(
                user=AuthUser(
                    provider_user_id=user.id,
                    email=user.email_addresses[0].email_address,
                    provider_type="clerk",
                    provider_metadata={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'image_url': user.image_url
                    }
                ),
                tokens=TokenPair(
                    access_token=session.last_active_token.jwt,
                    refresh_token=None,  # Clerk handles refresh internally
                    expires_at=datetime.fromtimestamp(
                        session.last_active_token.exp
                    )
                )
            )
        except Exception as e:
            raise InvalidCredentialsError(f"Authentication failed: {str(e)}")

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Clerk session token."""
        try:
            # Verify the JWT token with Clerk
            claims = self.clerk.verify_token(token)

            return {
                'user_id': claims['sub'],
                'session_id': claims['sid'],
                'email': claims.get('email')
            }
        except Exception:
            raise InvalidTokenError("Invalid or expired token")

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create user in Clerk."""
        try:
            user = self.clerk.users.create(
                email_addresses=[email],
                password=password,
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name')
            )

            return AuthUser(
                provider_user_id=user.id,
                email=email,
                provider_type="clerk",
                provider_metadata={
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            )
        except Exception as e:
            raise UserCreationError(f"Failed to create user: {str(e)}")

    async def send_password_reset(self, email: str) -> bool:
        """Send password reset email via Clerk."""
        try:
            # Find user by email
            users = self.clerk.users.list(email_addresses=[email])
            if not users:
                return False

            # Create password reset flow
            self.clerk.users.create_password_reset(
                user_id=users[0].id
            )
            return True
        except Exception:
            return False

    # Implement remaining protocol methods...
```

### Step 4: Configure Clerk

```python
# libs/clerk-auth/src/clerk_auth/config.py
from pydantic import BaseModel, Field

class ClerkConfig(BaseModel):
    """Configuration for Clerk auth provider."""
    publishable_key: str = Field(..., description="Clerk publishable key")
    secret_key: str = Field(..., description="Clerk secret key")
    jwt_verification_key: str = Field(..., description="JWT verification key")
    api_url: str = Field(
        default="https://api.clerk.com",
        description="Clerk API URL"
    )
```

### Step 5: Register Clerk Provider

```python
# libs/clerk-auth/src/clerk_auth/__init__.py
from core.domains.auth.factory import AuthProviderRegistry
from .provider import ClerkAuthProvider
from .config import ClerkConfig

def create_clerk_provider(config: dict) -> ClerkAuthProvider:
    clerk_config = ClerkConfig(**config)
    return ClerkAuthProvider(clerk_config)

# Auto-register
AuthProviderRegistry.register_provider("clerk", create_clerk_provider)
```

### Step 6: Frontend Clerk Integration

```typescript
// apps/web/lib/clerk-client.ts
import { ClerkProvider, useAuth } from '@clerk/nextjs'

export function ClerkAuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
      afterSignInUrl='/dashboard'
      afterSignUpUrl='/onboarding'
    >
      {children}
    </ClerkProvider>
  )
}

// Hook for accessing auth state
export function useClerkAuth() {
  const { isLoaded, userId, sessionId, getToken } = useAuth()

  return {
    isAuthenticated: !!userId,
    userId,
    sessionId,
    getAccessToken: async () => await getToken()
  }
}
```

## Example: Custom Auth System

### Complete Implementation Example

Here's a full example of a custom authentication system with database persistence:

```python
# libs/custom-auth/src/custom_auth/database.py
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "custom_users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SessionModel(Base):
    __tablename__ = "custom_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    access_token = Column(String, unique=True, nullable=False)
    refresh_token = Column(String, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = create_engine('postgresql://user:pass@localhost/authdb')
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
```

```python
# libs/custom-auth/src/custom_auth/provider.py
import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.domains.auth.protocols import AuthProvider
from core.domains.auth.schemas import AuthResult, AuthUser, TokenPair
from .database import SessionLocal, UserModel, SessionModel
from .config import CustomAuthConfig

class CustomAuthProvider(AuthProvider):
    """Production-ready custom authentication provider."""

    def __init__(self, config: CustomAuthConfig):
        self.config = config
        self.db: Session = SessionLocal()

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate user with bcrypt password verification."""
        # Find user in database
        user = self.db.query(UserModel).filter_by(email=email).first()

        if not user or not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise UserInactiveError("User account is inactive")

        # Generate tokens
        access_token = self._generate_token(user.id, 'access', hours=1)
        refresh_token = self._generate_token(user.id, 'refresh', days=30)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Store session
        session = SessionModel(
            id=secrets.token_urlsafe(16),
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.commit()

        return AuthResult(
            user=AuthUser(
                provider_user_id=user.id,
                email=user.email,
                provider_type="custom",
                provider_metadata={
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            ),
            tokens=TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
        )

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token with database session check."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=['HS256']
            )

            # Verify session exists and is valid
            session = self.db.query(SessionModel).filter_by(
                access_token=token
            ).first()

            if not session or session.expires_at < datetime.utcnow():
                raise InvalidTokenError("Token expired or invalid")

            # Get user info
            user = self.db.query(UserModel).filter_by(
                id=payload['user_id']
            ).first()

            return {
                'user_id': user.id,
                'email': user.email,
                'session_id': session.id
            }
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token."""
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                self.config.jwt_secret,
                algorithms=['HS256']
            )

            # Find session
            session = self.db.query(SessionModel).filter_by(
                refresh_token=refresh_token
            ).first()

            if not session:
                raise InvalidTokenError("Invalid refresh token")

            # Generate new access token
            new_access_token = self._generate_token(
                payload['user_id'], 'access', hours=1
            )
            new_expires_at = datetime.utcnow() + timedelta(hours=1)

            # Update session
            session.access_token = new_access_token
            session.expires_at = new_expires_at
            self.db.commit()

            return TokenPair(
                access_token=new_access_token,
                refresh_token=refresh_token,
                expires_at=new_expires_at
            )
        except Exception as e:
            raise InvalidTokenError(f"Token refresh failed: {str(e)}")

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create new user with bcrypt password hashing."""
        # Check if user exists
        existing = self.db.query(UserModel).filter_by(email=email).first()
        if existing:
            raise UserAlreadyExistsError(f"User {email} already exists")

        # Hash password
        password_hash = self._hash_password(password)

        # Create user
        user = UserModel(
            id=secrets.token_urlsafe(16),
            email=email,
            password_hash=password_hash,
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name')
        )
        self.db.add(user)
        self.db.commit()

        return AuthUser(
            provider_user_id=user.id,
            email=user.email,
            provider_type="custom",
            provider_metadata={
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        )

    async def logout(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """Logout user by invalidating session."""
        if session_id:
            # Invalidate specific session
            session = self.db.query(SessionModel).filter_by(
                id=session_id
            ).first()
            if session:
                self.db.delete(session)
        else:
            # Invalidate all user sessions
            self.db.query(SessionModel).filter_by(
                user_id=user_id
            ).delete()

        self.db.commit()
        return True

    async def send_password_reset(self, email: str) -> bool:
        """Send password reset email."""
        user = self.db.query(UserModel).filter_by(email=email).first()
        if not user:
            return False

        # Generate reset token (valid for 1 hour)
        reset_token = self._generate_token(
            user.id, 'password_reset', hours=1
        )

        # In production, send email with reset link
        # For now, just log the token
        print(f"Password reset token for {email}: {reset_token}")

        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        try:
            # Decode reset token
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=['HS256']
            )

            if payload.get('type') != 'password_reset':
                return False

            # Update user password
            user = self.db.query(UserModel).filter_by(
                id=payload['user_id']
            ).first()

            if not user:
                return False

            user.password_hash = self._hash_password(new_password)
            user.updated_at = datetime.utcnow()

            # Invalidate all existing sessions
            self.db.query(SessionModel).filter_by(
                user_id=user.id
            ).delete()

            self.db.commit()
            return True
        except Exception:
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def _verify_password(self, password: str, hash: str) -> bool:
        """Verify password against bcrypt hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hash.encode('utf-8')
        )

    def _generate_token(
        self, user_id: str, token_type: str,
        hours: int = 0, days: int = 0
    ) -> str:
        """Generate JWT token with expiration."""
        expiration = datetime.utcnow() + timedelta(hours=hours, days=days)

        payload = {
            'user_id': user_id,
            'type': token_type,
            'exp': expiration,
            'iat': datetime.utcnow()
        }

        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm='HS256'
        )

    # Implement remaining methods...
```

### Security Best Practices

When implementing a custom auth system, follow these security practices:

1. **Password Hashing**: Always use bcrypt or argon2 for password hashing
2. **Token Security**: Use strong secrets and short expiration times
3. **Rate Limiting**: Implement rate limiting on authentication endpoints
4. **Session Management**: Properly invalidate sessions on logout
5. **HTTPS Only**: Always use HTTPS in production
6. **Input Validation**: Validate and sanitize all inputs
7. **Audit Logging**: Log all authentication events
8. **2FA Support**: Consider adding two-factor authentication

## Suggested Improvements

After analyzing the authentication system, here are identified bugs and suggestions for improvement:

### 🐛 Bugs

1. **Token Storage Inconsistency**

   - **Issue**: Frontend stores tokens in both localStorage and cookies, leading to potential sync issues
   - **Location**: `apps/web/lib/auth.client.ts:94-107`
   - **Fix**: Use a single source of truth (preferably HTTP-only cookies for security)

2. **Missing Token Expiration Check**

   - **Issue**: Frontend doesn't check token expiration before making API calls
   - **Location**: `apps/web/lib/auth.client.ts`
   - **Fix**: Add token expiration validation and automatic refresh logic

3. **Race Condition in Session Creation**

   - **Issue**: Multiple simultaneous login attempts could create duplicate sessions
   - **Location**: `libs/core/src/core/domains/auth/service.py:43-46`
   - **Fix**: Add database-level unique constraints and proper transaction handling

4. **Middleware Bypass for Root Path**

   - **Issue**: Root path (`/`) is excluded from authentication checks
   - **Location**: `apps/web/middleware.ts:41`
   - **Fix**: Include root path in authentication logic or make it explicitly public

5. **Generic Exception Handling**
   - **Issue**: Provider validation catches all exceptions, not just auth-related ones
   - **Location**: `libs/core/src/core/domains/auth/service.py:65-70`
   - **Fix**: Catch specific exception types and handle accordingly

### 🔧 Security Improvements

1. **Add CSRF Protection**

   - Implement CSRF tokens for state-changing operations
   - Add double-submit cookie pattern for API requests

2. **Implement Rate Limiting**

   - Add rate limiting to authentication endpoints
   - Use Redis or in-memory store for tracking attempts

3. **Add Security Headers**

   - Implement security headers (CSP, HSTS, X-Frame-Options)
   - Add helmet.js for Next.js application

4. **Token Rotation**

   - Implement automatic token rotation on each use
   - Add token blacklisting for invalidated tokens

5. **Audit Logging**
   - Add comprehensive audit logging for all auth events
   - Include IP addresses, user agents, and timestamps

### 🚀 Performance Improvements

1. **Database Query Optimization**

   - Add indexes on frequently queried columns (email, provider_user_id)
   - Use select_related/prefetch_related for related data

2. **Caching Strategy**

   - Implement Redis caching for session validation
   - Cache user permissions and organization memberships

3. **Connection Pooling**
   - Configure proper database connection pooling
   - Add connection retry logic with exponential backoff

### 📦 Architectural Improvements

1. **Add Provider Health Checks**

   ```python
   class AuthProvider(Protocol):
       async def health_check(self) -> bool:
           """Check if provider is operational."""
           ...
   ```

2. **Implement Provider Fallback**

   ```python
   class FallbackAuthProvider(AuthProvider):
       """Fallback to secondary provider if primary fails."""
       def __init__(self, primary: AuthProvider, secondary: AuthProvider):
           self.primary = primary
           self.secondary = secondary
   ```

3. **Add Provider Metrics**

   - Track authentication success/failure rates
   - Monitor provider response times
   - Alert on abnormal patterns

4. **Standardize Error Responses**

   ```python
   class AuthError(BaseModel):
       code: str
       message: str
       details: Optional[Dict[str, Any]]
       timestamp: datetime
   ```

5. **Add Provider Webhooks**
   - Support webhooks for user events (created, updated, deleted)
   - Implement webhook signature verification

### 🧪 Testing Improvements

1. **Add Integration Tests**

   ```python
   async def test_full_auth_flow():
       # Test registration -> login -> refresh -> logout
       pass
   ```

2. **Add Provider Mock**

   ```python
   class MockAuthProvider(AuthProvider):
       """Mock provider for testing."""
       def __init__(self, users: List[AuthUser]):
           self.users = users
   ```

3. **Add Load Testing**
   - Test concurrent authentication attempts
   - Benchmark token validation performance

### 📝 Documentation Improvements

1. **Add API Documentation**

   - Generate OpenAPI specs for auth endpoints
   - Add request/response examples

2. **Add Migration Guides**

   - Document how to migrate from one provider to another
   - Include data migration scripts

3. **Add Troubleshooting Guide**
   - Common error messages and solutions
   - Debug logging configuration

### 🎯 Feature Additions

1. **Multi-Factor Authentication (MFA)**

   ```python
   class AuthProvider(Protocol):
       async def enable_mfa(self, user_id: str, method: str) -> bool:
           ...
       async def verify_mfa(self, user_id: str, code: str) -> bool:
           ...
   ```

2. **Social Login Support**

   - Add OAuth2 flow support
   - Implement provider linking

3. **Session Management UI**

   - Show active sessions to users
   - Allow session revocation

4. **Password Policy Enforcement**

   - Configurable password requirements
   - Password history tracking

5. **Account Recovery Options**
   - Security questions
   - Backup codes
   - Recovery email addresses

### 🔍 Monitoring Improvements

1. **Add Observability**

   ```python
   from opentelemetry import trace

   tracer = trace.get_tracer(__name__)

   @tracer.start_as_current_span("authenticate_user")
   async def authenticate_user(self, email: str, password: str):
       # Traced authentication logic
   ```

2. **Add Metrics Collection**

   - Authentication success/failure rates
   - Average response times
   - Token refresh patterns

3. **Add Alerting**
   - Alert on suspicious login patterns
   - Notify on provider failures
   - Monitor session anomalies

These improvements would significantly enhance the security, performance, and maintainability of the authentication system while maintaining its provider-agnostic architecture.
