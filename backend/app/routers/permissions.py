from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.deps import get_provider
from app.providers.base import ProjectProvider
from app.schemas import PermissionBulkRequest, PermissionBulkResult, PermissionsMatrix
from app.services.export import matrix_to_csv, matrix_to_xlsx
from app.services.permissions import apply_permissions, build_matrix, preview_permissions

router = APIRouter(tags=["permissions"])


def _matrix(provider: ProjectProvider, project_id: str) -> PermissionsMatrix:
    try:
        return build_matrix(provider, project_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="No se encontró el proyecto") from None


@router.get("/api/projects/{project_id}/permissions", response_model=PermissionsMatrix)
def permissions(project_id: str, provider: ProjectProvider = Depends(get_provider)):
    return _matrix(provider, project_id)


@router.get("/api/projects/{project_id}/permissions/export")
def export_permissions(
    project_id: str,
    file_format: str = Query("csv", alias="format"),
    provider: ProjectProvider = Depends(get_provider),
):
    matrix = _matrix(provider, project_id)
    filename = f"{matrix.project.code.lower()}-permisos"
    if file_format == "xlsx":
        return Response(
            content=matrix_to_xlsx(matrix),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )
    if file_format != "csv":
        raise HTTPException(status_code=400, detail="El formato debe ser csv o xlsx")
    return Response(
        content=matrix_to_csv(matrix),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


@router.post("/api/permissions/bulk/preview", response_model=PermissionBulkResult)
def preview(body: PermissionBulkRequest, provider: ProjectProvider = Depends(get_provider)):
    try:
        return preview_permissions(provider, body.project_id, body.folder_ids, body.role_id, body.level)
    except LookupError:
        raise HTTPException(status_code=404, detail="No se encontró el proyecto o el rol") from None


@router.post("/api/permissions/bulk/apply", response_model=PermissionBulkResult)
def apply(body: PermissionBulkRequest, provider: ProjectProvider = Depends(get_provider)):
    try:
        return apply_permissions(provider, body.project_id, body.folder_ids, body.role_id, body.level)
    except LookupError:
        raise HTTPException(status_code=404, detail="No se encontró el proyecto o el rol") from None
    except Exception:
        provider.rollback()
        raise
