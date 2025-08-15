"""Supabase authentication provider implementation."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import jwt
from core.domains.auth.protocols import AuthProvider
from core.domains.auth.schemas import (
    AuthProviderType,
    AuthResult,
    AuthUser,
    TokenPair,
)
from supabase import Client, create_client

from .config import SupabaseConfig


class SupabaseAuthProviderError(Exception):
    """Base exception for SupabaseAuthProvider errors."""

    pass


class SupabaseAuthProviderCredentialsError(SupabaseAuthProviderError):
    """Exception for authentication or signup failures."""

    def __init__(self, message: str):
        super().__init__(message)


class SupabaseAuthProviderTokenError(SupabaseAuthProviderError):
    """Exception for token validation or refresh failures."""

    def __init__(self, message: str):
        super().__init__(message)


logger = logging.getLogger("supabase_auth.provider")


class SupabaseAuthProvider(AuthProvider):
    """Supabase implementation of AuthProvider protocol."""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        logger.info(
            "Initializing SupabaseAuthProvider (url=%s)",
            config.supabase_api_url,
        )
        self.client: Client = create_client(
            config.supabase_api_url, config.supabase_public_key
        )
        self.admin_client: Client = create_client(
            config.supabase_api_url, config.supabase_secret_key
        )

    async def authenticate(self, email: str, password: str) -> AuthResult:
        """Authenticate with Supabase."""
        try:
            logger.info(
                "authenticate(str, str) -> AuthResult: Authenticating user via Supabase (email=%s)",
                email,
            )
            response = self.client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
            logger.info("Authentication successful (email=%s)", email)
            return self._convert_to_auth_result(response)

        except Exception as e:
            error_message = self._extract_error_message(e)
            logger.error(
                "authenticate(str, str) -> AuthResult: Error message: %s",
                error_message,
            )
            raise SupabaseAuthProviderCredentialsError(f"{error_message}")

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token with Supabase."""
        try:
            logger.info("Validating access token with Supabase")
            payload = jwt.decode(
                token,
                self.config.auth_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except Exception as e:
            error_message = self._extract_error_message(e)
            logger.error(
                "validate_token(str) -> Dict[str, Any]: Error message: %s",
                error_message,
            )
            raise SupabaseAuthProviderTokenError(f"{error_message}") from e

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh token with Supabase."""
        try:
            logger.info("Refreshing access token via Supabase")
            response = self.client.auth.refresh_session(
                {"refresh_token": refresh_token}
            )

            return TokenPair(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                expires_at=datetime.fromtimestamp(response.session.expires_at),
            )
        except Exception as e:
            logger.error(
                "refresh_token(str) -> TokenPair: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderTokenError(f"{error_message}") from e

    async def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Create user with Supabase."""
        try:
            logger.info("Creating user via Supabase (email=%s)", email)
            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": user_data},
                }
            )
            logger.info("User created via Supabase (email=%s)", email)
            return self._convert_user_to_auth_user(response.user)

        except Exception as e:
            logger.error(
                "create_user(str, str, Dict[str, Any]) -> AuthUser: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderCredentialsError(error_message)

    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID from Supabase."""
        try:
            logger.info(
                "get_user_by_id(str) -> Optional[AuthUser]: Fetching user by id via Supabase (user_id=%s)",
                user_id,
            )
            response = self.admin_client.auth.admin.get_user_by_id(user_id)
            return self._convert_user_to_auth_user(response.user)
        except Exception as e:
            logger.error(
                "get_user_by_id(str) -> Optional[AuthUser]: Error message: %s",
                str(e),
            )
            return None

    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email from Supabase."""
        try:
            logger.info(
                "get_user_by_email(str) -> Optional[AuthUser]: Fetching user by email via Supabase (email=%s)",
                email,
            )
            response = self.admin_client.auth.admin.list_users()
            for user in response.users:
                if user.email == email:
                    return self._convert_user_to_auth_user(user)
            return None
        except Exception as e:
            logger.error(
                "get_user_by_email(str) -> Optional[AuthUser]: Error message: %s",
                str(e),
            )
            return None

    async def update_user(
        self, user_id: str, user_data: Dict[str, Any]
    ) -> AuthUser:
        """Update user in Supabase."""
        try:
            logger.info("Updating user via Supabase (user_id=%s)", user_id)
            response = self.admin_client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": user_data},
            )

            return self._convert_user_to_auth_user(response.user)
        except Exception as e:
            logger.error(
                "update_user(str, Dict[str, Any]) -> AuthUser: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderCredentialsError(f"{error_message}")

    async def delete_user(self, user_id: str) -> bool:
        """Delete user from Supabase."""
        try:
            logger.info("Deleting user via Supabase (user_id=%s)", user_id)
            self.admin_client.auth.admin.delete_user(user_id)
            return True
        except Exception as e:
            logger.error(
                "delete_user(str) -> bool: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderCredentialsError(f"{error_message}")

    async def logout(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """Logout user from Supabase."""
        try:
            logger.info(
                "Logging out user via Supabase (user_id=%s, session_id=%s)",
                user_id,
                session_id,
            )
            self.client.auth.sign_out()
            return True
        except Exception as e:
            logger.error(
                "logout(str, Optional[str]) -> bool: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderCredentialsError(f"{error_message}")

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
            session_metadata=(
                {"supabase_session_id": str(supabase_response.session.id)}
                if hasattr(supabase_response.session, "id")
                and supabase_response.session.id is not None
                else {}
            ),
        )

    def _convert_user_to_auth_user(self, supabase_user) -> AuthUser:
        """Convert Supabase user to our AuthUser format."""
        if isinstance(supabase_user.created_at, str):
            created_at = datetime.fromisoformat(
                supabase_user.created_at.replace("Z", "+00:00")
            )
        elif isinstance(supabase_user.created_at, (int, float)):
            created_at = datetime.fromtimestamp(supabase_user.created_at)
        else:
            created_at = supabase_user.created_at

        if isinstance(supabase_user.updated_at, str):
            updated_at = datetime.fromisoformat(
                supabase_user.updated_at.replace("Z", "+00:00")
            )
        elif isinstance(supabase_user.updated_at, (int, float)):
            updated_at = datetime.fromtimestamp(supabase_user.updated_at)
        else:
            updated_at = supabase_user.updated_at

        return AuthUser(
            provider_user_id=supabase_user.id,
            email=supabase_user.email,
            provider_type=AuthProviderType.SUPABASE,
            provider_metadata={
                "supabase_data": supabase_user.user_metadata or {},
                "app_metadata": supabase_user.app_metadata or {},
            },
            created_at=created_at,
            updated_at=updated_at,
        )

    async def send_password_reset(self, email: str) -> bool:
        """Send password reset email via Supabase."""
        try:
            logger.info(
                "send_password_reset(str) -> bool: Sending password reset email via Supabase (email=%s)",
                email,
            )
            self.client.auth.reset_password_email({"email": email})
            logger.info(
                "Password reset email sent via Supabase (email=%s)", email
            )
            return True
        except Exception as e:
            logger.error(
                "send_password_reset(str) -> bool: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderCredentialsError(f"{error_message}")

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token."""
        try:
            # Verify recovery token and then update password in the verified session
            self.client.auth.verify_otp({"token": token, "type": "recovery"})
            self.client.auth.update_user({"password": new_password})
            return True
        except Exception as e:
            logger.error(
                "reset_password(str, str) -> bool: Error message: %s",
                str(e),
            )
            error_message = self._extract_error_message(e)
            raise SupabaseAuthProviderCredentialsError(f"{error_message}")

    def _extract_error_message(self, exc: Exception) -> str:
        """Extract a human-readable error message from an exception."""
        if hasattr(exc, "args") and exc.args:
            return str(exc.args[0])
        return str(exc)
