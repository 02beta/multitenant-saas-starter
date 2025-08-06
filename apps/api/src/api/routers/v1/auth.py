"""Authentication API routes."""

import secrets

from api.utils import handle_domain_exception
from core.common.exceptions import DomainException
from core.database import get_session
from core.domains.users import (
    PasswordService,
    UserRepository,
    UserService,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy in-memory token store for demonstration
fake_tokens = {}


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    """Get UserService instance with dependencies."""
    user_repository = UserRepository()
    password_service = PasswordService()
    return UserService(user_repository, password_service)


def authenticate_user(
    email: str, password: str, user_service: UserService = Depends(get_user_service)
):
    """Authenticate a user by email and password."""
    return user_service.authenticate_user(
        user_service.session, email=email, password=password
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
):
    """Get the current authenticated user from token."""
    user_email = fake_tokens.get(token)
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user = user_service.get_user_by_email(user_service.session, email=user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """Login endpoint to get access token."""
    try:
        user = authenticate_user(form_data.username, form_data.password, user_service)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        token = secrets.token_urlsafe(32)
        fake_tokens[token] = user.email  # Store email instead of username
        return {"access_token": token, "token_type": "bearer"}
    except DomainException as exc:
        return handle_domain_exception(exc)
