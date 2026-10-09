import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.deps import get_provider
from app.providers.base import ProjectProvider
from app.schemas import MemberOut, ProjectDetail, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_out(provider: ProjectProvider, project, members: list | None = None) -> ProjectOut | ProjectDetail:
    folders = provider.list_folders(project.id)
    found = members if members is not None else provider.list_memberships(project.id)
    payload = dict(
        id=project.id,
        name=project.name,
        code=project.code,
        status=project.status,
        location=project.location,
        client=project.client,
        phase=project.phase,
        created_at=project.created_at,
        folder_count=len(folders),
        member_count=len(found),
    )
    if members is None:
        return ProjectOut(**payload)
    return ProjectDetail(
        **payload,
        members=[
            MemberOut(
                user_id=item.user.id,
                name=item.user.name,
                email=item.user.email,
                company=item.user.company,
                role_id=item.role.id,
                role=item.role.name,
            )
            for item in members
        ],
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(provider: ProjectProvider = Depends(get_provider)):
    return [_project_out(provider, project) for project in provider.list_projects()]


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, provider: ProjectProvider = Depends(get_provider)):
    project = provider.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="No se encontró el proyecto")
    return _project_out(provider, project, provider.list_memberships(project.id))


@router.get("/{project_id}/metadata")
def download_metadata(project_id: str, provider: ProjectProvider = Depends(get_provider)):
    project = provider.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="No se encontró el proyecto")
    detail = _project_out(provider, project, provider.list_memberships(project.id))
    payload = {
        "proyecto": detail.model_dump(mode="json"),
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "nota": "Metadatos ficticios generados por la demostración Senda.",
    }
    filename = f"{project.code.lower()}-metadatos.json"
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
