"""V1 API router."""

from api.routers.v1.memberships import router as memberships_router
from api.routers.v1.organizations import router as organizations_router
from api.routers.v1.users import router as users_router
from fastapi import APIRouter

router = APIRouter(prefix="/v1")

router.include_router(users_router)
router.include_router(organizations_router)
router.include_router(memberships_router)

# Export as v1_router for clarity
v1_router = router

__all__ = ["v1_router"]
