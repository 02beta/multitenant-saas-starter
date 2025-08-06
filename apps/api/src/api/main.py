# apps/api/src/api/main.py

import secrets
from contextlib import asynccontextmanager

from api.routers import v1_router
from api.utils import handle_domain_exception
from core.common.exceptions import DomainException
from core.database import create_tables, get_session
from core.domains.memberships import (
    MembershipRepository,
    MembershipService,
)
from core.domains.organizations import (
    OrganizationRepository,
    OrganizationService,
)
from core.domains.users import (
    PasswordService,
    UserRepository,
    UserService,
)
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    print("Starting up API...")
    create_tables()
    print("Database tables created successfully")

    yield

    # Shutdown
    print("Shutting down API...")
    # Add any cleanup logic here (close connections, etc.)
    print("Shutdown complete")


app = FastAPI(title="API", version="0.1.0", lifespan=lifespan)

# Include API routers
app.include_router(v1_router, prefix="")

# --- Auth ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy in-memory token store for demonstration
fake_tokens = {}


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    """Get UserService instance with dependencies."""
    user_repository = UserRepository()
    password_service = PasswordService()
    return UserService(user_repository, password_service)


def get_organization_service() -> OrganizationService:
    """Get OrganizationService instance."""
    organization_repository = OrganizationRepository()
    return OrganizationService(organization_repository)


def get_membership_service() -> MembershipService:
    """Get MembershipService instance."""
    membership_repository = MembershipRepository()
    return MembershipService(membership_repository)


def authenticate_user(email: str, password: str, session: Session):
    user_service = get_user_service(session)
    return user_service.authenticate_user(session, email=email, password=password)


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
):
    user_email = fake_tokens.get(token)
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user_service = get_user_service(session)
    user = user_service.get_user_by_email(session, email=user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


# --- Exception Handling ---


@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc: DomainException):
    return handle_domain_exception(exc)


# --- Root and Health ---


@app.get("/")
async def root():
    return {"message": "Hello from API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# --- Auth Route ---


@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = secrets.token_urlsafe(32)
    fake_tokens[token] = user.email  # Store email instead of username
    return {"access_token": token, "token_type": "bearer"}
