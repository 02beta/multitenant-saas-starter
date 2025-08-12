"""Provider factory with registration system."""

from typing import Any, Callable, Dict

# from .exceptions import UnsupportedAuthProviderError
from .protocols import AuthProvider, AuthProviderStub


class AuthProviderRegistry:
    """Registry for authentication providers."""

    _providers: Dict[str, Callable[..., AuthProvider]] = {}

    @classmethod
    def register_provider(
        cls, name: str, provider_factory: Callable[..., AuthProvider]
    ) -> None:
        """Register an authentication provider factory."""
        cls._providers[name] = provider_factory
        print(f"Registered auth provider: {name}")

    @classmethod
    def create_provider(
        cls, provider_name: str, config: Dict[str, Any]
    ) -> AuthProvider:
        """Create provider instance."""
        if provider_name not in cls._providers:
            print(
                f"Warning: Provider '{provider_name}' not registered, using stub"
            )
            return AuthProviderStub()

        factory = cls._providers[provider_name]
        return factory(config)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def is_provider_registered(cls, provider_name: str) -> bool:
        """Check if provider is registered."""
        return provider_name in cls._providers
