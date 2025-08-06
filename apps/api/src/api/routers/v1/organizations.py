"""Organization API routes."""

from typing import List
from uuid import UUID

from api.utils import handle_domain_exception
from core.common.exceptions import DomainException
from core.database import get_session
from core.domains.organizations import (
    OrganizationCreate,
    OrganizationPublic,
    OrganizationRepository,
    OrganizationService,
    OrganizationUpdate,
)
from core.domains.users import User
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_organization_service() -> OrganizationService:
    """Get OrganizationService instance."""
    organization_repository = OrganizationRepository()
    return OrganizationService(organization_repository)


def get_current_user() -> User:
    """Placeholder for current user dependency."""
    # This should be replaced with actual authentication logic
    pass


@router.post("/", response_model=OrganizationPublic)
async def create_organization(
    organization: OrganizationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Create a new organization."""
    try:
        return await organization_service.create_organization(
            session, organization_data=organization, created_by_id=current_user.id
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/", response_model=List[OrganizationPublic])
async def list_user_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """List organizations for the current user."""
    try:
        return await organization_service.get_user_organizations(
            session, user_id=current_user.id
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/{organization_id}", response_model=OrganizationPublic)
async def get_organization(
    organization_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Get a specific organization by ID."""
    try:
        organization = await organization_service.get_organization(
            session, organization_id=organization_id
        )
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        return organization
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/slug/{slug}", response_model=OrganizationPublic)
async def get_organization_by_slug(
    slug: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Get a specific organization by slug."""
    try:
        organization = await organization_service.get_organization_by_slug(
            session, slug=slug
        )
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        return organization
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.put("/{organization_id}", response_model=OrganizationPublic)
async def update_organization(
    organization_id: UUID,
    organization_update: OrganizationUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Update a organization."""
    try:
        existing_organization = await organization_service.get_organization(
            session, organization_id=organization_id
        )
        if not existing_organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

        return await organization_service.update_organization(
            session, organization=existing_organization, update_data=organization_update
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Soft delete a organization."""
    try:
        existing_organization = await organization_service.get_organization(
            session, organization_id=organization_id
        )
        if not existing_organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

        success = await organization_service.delete_organization(
            session, organization_id=organization_id, deleted_by_id=current_user.id
        )

        if success:
            return {"message": "Organization deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete organization",
            )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/search/by-name", response_model=List[OrganizationPublic])
async def search_organizations_by_name(
    search_term: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Search organizations by name."""
    try:
        organization_repository = OrganizationRepository()
        return organization_repository.search_by_name(
            session, search_term=search_term, limit=limit
        )
    except DomainException as exc:
        return handle_domain_exception(exc)


@router.get("/plan/{plan_name}", response_model=List[OrganizationPublic])
async def get_organizations_by_plan(
    plan_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Get all active organizations on a specific plan."""
    try:
        organization_repository = OrganizationRepository()
        return organization_repository.get_active_organizations_by_plan(
            session, plan_name=plan_name
        )
    except DomainException as exc:
        return handle_domain_exception(exc)
