"""Service for the users domain."""

import hashlib
import re
import secrets
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from .exceptions import (
    InvalidEmailFormatError,
    UserAlreadyExistsError,
    WeakPasswordError,
)
from .models import User, UserCreate, UserPublic, UserUpdate
from .repository import UserRepository


class PasswordService:
    """Service for password operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using PBKDF2 with SHA-256.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        # Generate a random salt
        salt = secrets.token_hex(32)

        # Hash the password with the salt
        pwdhash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # 100k iterations
        )

        return f"{salt}:{pwdhash.hex()}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed_password: Stored hashed password

        Returns:
            True if password is valid, False otherwise
        """
        try:
            salt, pwdhash = hashed_password.split(":")
            return secrets.compare_digest(
                pwdhash,
                hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt.encode("utf-8"),
                    100000,
                ).hex(),
            )
        except ValueError:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Validate password strength requirements.

        Args:
            password: Password to validate

        Raises:
            WeakPasswordError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise WeakPasswordError("Password must be at least 8 characters long")

        if len(password) > 128:
            raise WeakPasswordError("Password must be no more than 128 characters long")

        if not re.search(r"[A-Z]", password):
            raise WeakPasswordError(
                "Password must contain at least one uppercase letter"
            )

        if not re.search(r"[a-z]", password):
            raise WeakPasswordError(
                "Password must contain at least one lowercase letter"
            )

        if not re.search(r"\d", password):
            raise WeakPasswordError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise WeakPasswordError(
                "Password must contain at least one special character"
            )

        # Check for common weak passwords
        common_passwords = {
            "password",
            "123456",
            "12345678",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
        }
        if password.lower() in common_passwords:
            raise WeakPasswordError("Password is too common and easily guessable")

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Length of the password (minimum 12)

        Returns:
            Secure random password
        """
        if length < 12:
            length = 12

        # Define character sets
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        digits = "0123456789"
        special = '!@#$%^&*(),.?":{}|<>'

        # Ensure at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        # Fill the rest randomly
        all_chars = uppercase + lowercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        return "".join(password)


class UserService:
    """Service for User domain operations."""

    def __init__(
        self,
        repository: UserRepository,
        password_service: PasswordService,
    ):
        """
        Initialize the service with a repository.

        Args:
            repository: UserRepository instance
        """
        self.repository = repository
        self.password_service = password_service

    def create_user(
        self,
        session: Session,
        *,
        user_in: UserCreate,
        created_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Create a new user with validation and password hashing.

        Args:
            session: Database session
            user_in: User creation data
            created_by_id: ID of the user creating this user (optional)

        Returns:
            Created User instance

        Raises:
            UserAlreadyExistsError: If email already exists
            InvalidEmailFormatError: If email format is invalid
            WeakPasswordError: If password doesn't meet requirements
        """
        # Validate email format
        if not self.repository.validate_email_format(user_in.email):
            raise InvalidEmailFormatError(user_in.email)

        # Check if user already exists
        if self.repository.check_email_exists(session, email=user_in.email):
            raise UserAlreadyExistsError(user_in.email)

        # Validate password strength
        self.password_service.validate_password_strength(user_in.password)

        # Hash the password
        hashed_password = self.password_service.hash_password(user_in.password)

        # Create user data
        create_data = user_in.model_dump()
        create_data["password"] = hashed_password

        if created_by_id:
            create_data["created_by"] = created_by_id

        # Create the user
        user = User(**create_data)
        return self.repository.create(session, obj_in=user)

    def get_user(self, session: Session, *, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            User instance or None if not found
        """
        return self.repository.get(session, user_id)

    def get_user_by_email(self, session: Session, *, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            session: Database session
            email: User's email address

        Returns:
            User instance or None if not found
        """
        return self.repository.get_by_email(session, email=email)

    def authenticate_user(
        self, session: Session, *, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Args:
            session: Database session
            email: User's email address
            password: Plain text password

        Returns:
            User instance if authentication successful, None otherwise
        """
        user = self.repository.get_by_email(session, email=email)

        if not user:
            return None

        if not user.is_active:
            return None

        if not self.password_service.verify_password(password, user.password):
            return None

        return user

    def update_user(
        self,
        session: Session,
        *,
        user: User,
        user_in: UserUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Update user with validation.

        Args:
            session: Database session
            user: User instance to update
            user_in: User update data
            updated_by_id: ID of the user making the update

        Returns:
            Updated User instance

        Raises:
            UserAlreadyExistsError: If new email already exists
            InvalidEmailFormatError: If new email format is invalid
            WeakPasswordError: If new password doesn't meet requirements
        """
        update_data = user_in.model_dump(exclude_unset=True)

        # Validate email if being updated
        if "email" in update_data:
            new_email = update_data["email"]
            if not self.repository.validate_email_format(new_email):
                raise InvalidEmailFormatError(new_email)

            # Check if new email already exists
            if self.repository.check_email_exists(
                session, email=new_email, exclude_user_id=user.id
            ):
                raise UserAlreadyExistsError(new_email)

        # Validate and hash password if being updated
        if "password" in update_data:
            new_password = update_data["password"]
            self.password_service.validate_password_strength(new_password)
            update_data["password"] = self.password_service.hash_password(new_password)

        return self.repository.update(
            session,
            db_obj=user,
            obj_in=UserUpdate(**update_data),
            updated_by_id=updated_by_id,
        )

    def change_password(
        self,
        session: Session,
        *,
        user: User,
        current_password: str,
        new_password: str,
        updated_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Change user's password with current password verification.

        Args:
            session: Database session
            user: User instance
            current_password: Current password for verification
            new_password: New password
            updated_by_id: ID of the user making the change

        Returns:
            Updated User instance

        Raises:
            WeakPasswordError: If current password is wrong or new password is weak
        """
        # Verify current password
        if not self.password_service.verify_password(current_password, user.password):
            raise WeakPasswordError("Current password is incorrect")

        # Validate new password
        self.password_service.validate_password_strength(new_password)

        # Hash new password
        update_data = UserUpdate(
            password=self.password_service.hash_password(new_password)
        )

        # Update password
        return self.repository.update(
            session, db_obj=user, obj_in=update_data, updated_by_id=updated_by_id
        )

    def deactivate_user(
        self,
        session: Session,
        *,
        user: User,
        deactivated_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Deactivate a user account.

        Args:
            session: Database session
            user: User instance to deactivate
            deactivated_by_id: ID of the user performing the deactivation

        Returns:
            Updated User instance
        """
        update_data = UserUpdate(is_active=False)
        return self.repository.update(
            session, db_obj=user, obj_in=update_data, updated_by_id=deactivated_by_id
        )

    def activate_user(
        self,
        session: Session,
        *,
        user: User,
        activated_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Activate a user account.

        Args:
            session: Database session
            user: User instance to activate
            activated_by_id: ID of the user performing the activation

        Returns:
            Updated User instance
        """
        update_data = UserUpdate(is_active=True)
        return self.repository.update(
            session, db_obj=user, obj_in=update_data, updated_by_id=activated_by_id
        )

    def delete_user(
        self,
        session: Session,
        *,
        user_id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """
        Soft delete a user.

        Args:
            session: Database session
            user_id: User ID to delete
            deleted_by_id: ID of the user performing the deletion

        Returns:
            True if successful
        """
        return self.repository.remove(session, id=user_id, deleted_by_id=deleted_by_id)

    def get_users(
        self,
        session: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[UserPublic]:
        """
        Get multiple users with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to return only active users

        Returns:
            List of UserPublic instances
        """
        if active_only:
            users = self.repository.get_active_users(session, skip=skip, limit=limit)
        else:
            users = self.repository.get_multi(session, skip=skip, limit=limit)

        # Convert to public schema (exclude password)
        return [
            UserPublic(
                id=user.id,
                email=user.email,
                password="",  # Never expose password
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]

    def search_users(
        self, session: Session, *, search_term: str, limit: int = 10
    ) -> List[UserPublic]:
        """
        Search users by name or email.

        Args:
            session: Database session
            search_term: Search term
            limit: Maximum number of results

        Returns:
            List of UserPublic instances
        """
        users = self.repository.search_users(
            session, search_term=search_term, limit=limit
        )

        # Convert to public schema
        return [
            UserPublic(
                id=user.id,
                email=user.email,
                password="",  # Never expose password
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]

    def get_user_count(self, session: Session, *, active_only: bool = True) -> int:
        """
        Get total count of users.

        Args:
            session: Database session
            active_only: Whether to count only active users

        Returns:
            Total number of users
        """
        return self.repository.count_users(session, active_only=active_only)

    def promote_to_superuser(
        self,
        session: Session,
        *,
        user: User,
        promoted_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Promote user to superuser status.

        Args:
            session: Database session
            user: User instance to promote
            promoted_by_id: ID of the user performing the promotion

        Returns:
            Updated User instance
        """
        update_data = UserUpdate(is_superuser=True)
        return self.repository.update(
            session, db_obj=user, obj_in=update_data, updated_by_id=promoted_by_id
        )

    def revoke_superuser(
        self,
        session: Session,
        *,
        user: User,
        revoked_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Revoke superuser status from user.

        Args:
            session: Database session
            user: User instance to revoke from
            revoked_by_id: ID of the user performing the revocation

        Returns:
            Updated User instance
        """
        update_data = UserUpdate(is_superuser=False)
        return self.repository.update(
            session, db_obj=user, obj_in=update_data, updated_by_id=revoked_by_id
        )
