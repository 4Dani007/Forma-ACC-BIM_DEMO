from app.providers.base import ProjectProvider
from app.schemas import (
    FolderRow,
    PermissionBulkResult,
    PermissionPlanRow,
    PermissionsMatrix,
    ProjectRef,
    RoleOut,
)


def build_matrix(provider: ProjectProvider, project_id: str) -> PermissionsMatrix:
    project = provider.get_project(project_id)
    if project is None:
        raise LookupError(project_id)

    roles = provider.list_roles()
    folders = provider.list_folders(project_id)
    indexed: dict[str, dict[str, str]] = {folder.id: {} for folder in folders}
    for permission in provider.list_permissions(project_id):
        indexed[permission.folder_id][permission.role_id] = permission.level

    return PermissionsMatrix(
        project=ProjectRef(id=project.id, name=project.name, code=project.code),
        roles=[RoleOut(id=role.id, name=role.name) for role in roles],
        folders=[
            FolderRow(
                id=folder.id,
                name=folder.name,
                path=folder.path,
                depth=folder.depth,
                parent_id=folder.parent_id,
                permissions=indexed[folder.id],
            )
            for folder in folders
        ],
    )


def preview_permissions(
    provider: ProjectProvider,
    project_id: str,
    folder_ids: list[str],
    role_id: str,
    level: str,
) -> PermissionBulkResult:
    project = provider.get_project(project_id)
    if project is None:
        raise LookupError(project_id)
    role = provider.get_role(role_id)
    if role is None:
        raise LookupError(role_id)

    folders = {folder.id: folder for folder in provider.list_folders(project_id)}
    rows: list[PermissionPlanRow] = []
    for folder_id in folder_ids:
        folder = folders.get(folder_id)
        if folder is None:
            rows.append(
                PermissionPlanRow(
                    folder_id=folder_id,
                    path=folder_id,
                    role=role.name,
                    level_before=None,
                    level_after=None,
                    status="rejected",
                    message="La carpeta no pertenece a este proyecto.",
                )
            )
            continue
        current = provider.get_permission(folder.id, role.id)
        before = current.level if current else None
        if before == level:
            status = "unchanged"
            message = f"{folder.path} ya tiene «{level}» para {role.name}."
        elif before is None:
            status = "new"
            message = f"{folder.path} pasará a «{level}» para {role.name}."
        else:
            status = "change"
            message = f"{folder.path} cambiará de «{before}» a «{level}» para {role.name}."
        rows.append(
            PermissionPlanRow(
                folder_id=folder.id,
                path=folder.path,
                role=role.name,
                level_before=before,
                level_after=level,
                status=status,
                message=message,
            )
        )
    return PermissionBulkResult(rows=rows, summary=_count(rows))


def apply_permissions(
    provider: ProjectProvider,
    project_id: str,
    folder_ids: list[str],
    role_id: str,
    level: str,
) -> PermissionBulkResult:
    planned = preview_permissions(provider, project_id, folder_ids, role_id, level)
    applied = 0
    for item in planned.rows:
        if item.status not in {"new", "change"}:
            continue
        provider.upsert_permission(item.folder_id, role_id, level)
        applied += 1

    provider.add_audit(
        "bulk_permissions",
        {
            "mensaje": "Cambio masivo de permisos.",
            "project_id": project_id,
            "role_id": role_id,
            "level": level,
            "aplicadas": applied,
            "sin_cambio": planned.summary["unchanged"],
            "rechazadas": planned.summary["rejected"],
            "filas": [item.model_dump() for item in planned.rows],
        },
    )
    provider.commit()
    planned.summary["applied"] = applied
    return planned


def _count(rows: list[PermissionPlanRow]) -> dict[str, int]:
    return {
        "total": len(rows),
        "new": sum(row.status == "new" for row in rows),
        "change": sum(row.status == "change" for row in rows),
        "unchanged": sum(row.status == "unchanged" for row in rows),
        "rejected": sum(row.status == "rejected" for row in rows),
    }
