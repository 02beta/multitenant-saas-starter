"""Organization domain specific exceptions."""

from core.common.exceptions import AlreadyExistsError, ValidationError


class OrganizationAlreadyExistsError(AlreadyExistsError):
    """Raised when attempting to create a organization with a slug that already exists."""

    def __init__(self, slug: str):
        """
        Initialize organization already exists error.

        Args:
            slug: The slug that already exists
        """
        super().__init__(resource="Organization", field="slug", value=slug)


class InvalidOrganizationSlugError(ValidationError):
    """Raised when a organization slug format is invalid."""

    def __init__(self, slug: str):
        """
        Initialize invalid organization slug error.

        Args:
            slug: The invalid slug
        """
        super().__init__(
            message="Invalid slug format. Use lowercase letters, numbers, and hyphens only.",
            field="slug",
        )
