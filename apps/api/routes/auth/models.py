from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str
    organization_id: Optional[UUID] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: Optional[int]
    user: dict
    organization_slug: Optional[str] = None


class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company_size: Optional[str] = None
    organization_name: str
    slug: str


class SignupResponse(SignupRequest):
    organization_id: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str
    redirect_url: Optional[str] = None
