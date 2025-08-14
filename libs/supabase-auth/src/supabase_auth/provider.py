"""Supabase authentication provider implementation."""

from datetime import datetime
from typing import Any, Dict, Optional

import jwt
from core.domains.auth.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
)
from core.domains.auth.protocols import AuthProvider
from core.domains.auth.schemas import (
    AuthProviderType,
    AuthResult,
    AuthUser,
    TokenPair,
)
from supabase import Client, create_client

from .config import SupabaseConfig


class SupabaseAuthProvider(AuthProvider):
    """Supabase implementation of AuthProvider protocol."""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.client: Client = create_client(
            config.supabase_api_url, config.supabase_public_key
        )
        self.admin_client: Client = create_client(
            config.supabase_api_url, config.supabase_secret_key
        )

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate with Supabase."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            return self._convert_to_auth_result(response)

        except Exception as e:
            raise InvalidCredentialsError() from e

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token with Supabase."""
        try:
            payload = jwt.decode(
                token,
                self.config.auth_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except Exception as e:
            raise InvalidTokenError() from e

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh token with Supabase."""
        try:
            response = self.client.auth.refresh_session(refresh_token)

            return TokenPair(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                expires_at=datetime.fromtimestamp(response.session.expires_at),
            )
        except Exception as e:
            raise InvalidTokenError() from e

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create user with Supabase."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": user_data},
            })

            return self._convert_user_to_auth_user(response.user)

        except Exception as e:
            raise InvalidCredentialsError() from e

    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID from Supabase."""
        # Implementation would use Supabase admin client
        try:
            response = self.admin_client.auth.admin.get_user_by_id(user_id)
            return self._convert_user_to_auth_user(response.user)
        except Exception:
            return None

    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email from Supabase."""
        # Implementation would use Supabase admin client
        try:
            response = self.admin_client.auth.admin.list_users()
            for user in response.users:
                if user.email == email:
                    return self._convert_user_to_auth_user(user)
            return None
        except Exception:
            return None

    async def update_user(
        self, user_id: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Update user in Supabase."""
        try:
            response = self.client.auth.update_user({"data": user_data})

            return self._convert_user_to_auth_user(response.user)
        except Exception as e:
            raise InvalidCredentialsError() from e

    async def delete_user(self, user_id: str) -> bool:
        """Delete user from Supabase."""
        try:
            self.admin_client.auth.admin.delete_user(user_id)
            return True
        except Exception:
            return False

    async def logout(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """Logout user from Supabase."""
        try:
            self.client.auth.sign_out()
            return True
        except Exception:
            return False

    def _convert_to_auth_result(self, supabase_response) -> AuthResult:
        """Convert Supabase response to our AuthResult format."""
        user = self._convert_user_to_auth_user(supabase_response.user)
        tokens = TokenPair(
            access_token=supabase_response.session.access_token,
            refresh_token=supabase_response.session.refresh_token,
            expires_at=datetime.fromtimestamp(
                supabase_response.session.expires_at
            ),
        )

        return AuthResult(
            user=user,
            tokens=tokens,
            session_metadata={
                "supabase_session_id": str(supabase_response.session.id)
            },
        )

    def _convert_user_to_auth_user(self, supabase_user) -> AuthUser:
        """Convert Supabase user to our AuthUser format."""
        return AuthUser(
            provider_user_id=supabase_user.id,
            email=supabase_user.email,
            provider_type=AuthProviderType.SUPABASE,
            provider_metadata={
                "supabase_data": supabase_user.user_metadata,
                "app_metadata": supabase_user.app_metadata,
            },
            created_at=datetime.fromisoformat(
                supabase_user.created_at.replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                supabase_user.updated_at.replace("Z", "+00:00")
            ),
        )

    async def send_password_reset(self, email: str) -> bool:
        """Send password reset email via Supabase."""
        try:
            self.client.auth.reset_password_email(email)
            return True
        except Exception:
            return False

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token."""
        try:
            self.client.auth.update_user({"password": new_password})
            return True
        except Exception:
            return False
