from fastapi import APIRouter, Depends

from app.deps import get_provider
from app.providers.base import ProjectProvider
from app.schemas import MembershipBulkRequest, MembershipBulkResult, RoleOut
from app.services.bulk import apply_memberships, preview_memberships

router = APIRouter(tags=["memberships"])


@router.get("/api/roles", response_model=list[RoleOut])
def list_roles(provider: ProjectProvider = Depends(get_provider)):
    return [RoleOut(id=role.id, name=role.name) for role in provider.list_roles()]


@router.post("/api/memberships/bulk/preview", response_model=MembershipBulkResult)
def preview(body: MembershipBulkRequest, provider: ProjectProvider = Depends(get_provider)):
    return preview_memberships(provider, body.rows)


@router.post("/api/memberships/bulk/apply", response_model=MembershipBulkResult)
def apply(body: MembershipBulkRequest, provider: ProjectProvider = Depends(get_provider)):
    try:
        return apply_memberships(provider, body.rows)
    except Exception:
        provider.rollback()
        raise
