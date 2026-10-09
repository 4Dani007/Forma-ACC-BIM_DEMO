from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_provider
from app.providers.base import ProjectProvider
from app.schemas import AuditOut, CompareResult, ResetOut
from app.seed import reset_database
from app.services.compare import compare_projects

router = APIRouter(tags=["compare"])


@router.get("/api/compare", response_model=CompareResult)
def compare(a: str, b: str, provider: ProjectProvider = Depends(get_provider)):
    try:
        return compare_projects(provider, a, b)
    except LookupError:
        raise HTTPException(status_code=404, detail="No se encontró uno de los proyectos") from None


@router.get("/api/audit", response_model=list[AuditOut])
def audit(limit: int = 100, provider: ProjectProvider = Depends(get_provider)):
    safe_limit = min(max(limit, 1), 200)
    return [
        AuditOut(
            id=entry.id,
            action=entry.action,
            actor=entry.actor,
            detail=entry.detail,
            created_at=entry.created_at,
        )
        for entry in provider.list_audit(safe_limit)
    ]


@router.post("/api/demo/reset", response_model=ResetOut)
def reset_demo(db: Session = Depends(get_db)):
    return reset_database(db)
