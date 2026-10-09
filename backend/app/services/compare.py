from app.providers.base import ProjectProvider
from app.schemas import (
    CompareDiff,
    CompareResult,
    CompareRow,
    CompareSummary,
    ProjectRef,
)

def compare_projects(provider: ProjectProvider, project_a_id: str, project_b_id: str) -> CompareResult:
    project_a = provider.get_project(project_a_id)
    project_b = provider.get_project(project_b_id)
    if project_a is None or project_b is None:
        missing = project_a_id if project_a is None else project_b_id
        raise LookupError(missing)

    folders_a = {folder.path: folder for folder in provider.list_folders(project_a.id)}
    folders_b = {folder.path: folder for folder in provider.list_folders(project_b.id)}
    roles = provider.list_roles()
    perms_a = _index(provider.list_permissions(project_a.id))
    perms_b = _index(provider.list_permissions(project_b.id))

    rows: list[CompareRow] = []
    for path in sorted(set(folders_a) | set(folders_b)):
        folder_a = folders_a.get(path)
        folder_b = folders_b.get(path)
        existing = folder_a or folder_b
        permissions_a = _levels(folder_a, roles, perms_a)
        permissions_b = _levels(folder_b, roles, perms_b)

        if folder_a and not folder_b:
            status = "missing_in_b"
            diffs: list[CompareDiff] = []
        elif folder_b and not folder_a:
            status = "missing_in_a"
            diffs = []
        else:
            diffs = []
            for role in roles:
                level_a = perms_a.get((folder_a.id, role.id))
                level_b = perms_b.get((folder_b.id, role.id))
                if level_a == level_b:
                    continue
                kind = "role_missing" if level_a is None or level_b is None else "permission_mismatch"
                diffs.append(CompareDiff(role=role.name, level_a=level_a, level_b=level_b, kind=kind))
            status = _status_from_diffs(diffs)

        rows.append(
            CompareRow(
                path=path,
                name=existing.name,
                depth=existing.depth,
                status=status,
                permissions_a=permissions_a,
                permissions_b=permissions_b,
                diffs=diffs,
            )
        )

    summary = CompareSummary(
        total=len(rows),
        same=sum(row.status == "same" for row in rows),
        permission_mismatch=sum(row.status == "permission_mismatch" for row in rows),
        role_missing=sum(row.status == "role_missing" for row in rows),
        missing_in_a=sum(row.status == "missing_in_a" for row in rows),
        missing_in_b=sum(row.status == "missing_in_b" for row in rows),
    )
    return CompareResult(
        project_a=ProjectRef(id=project_a.id, name=project_a.name, code=project_a.code),
        project_b=ProjectRef(id=project_b.id, name=project_b.name, code=project_b.code),
        summary=summary,
        rows=rows,
    )


def _index(permissions) -> dict[tuple[str, str], str]:
    return {(item.folder_id, item.role_id): item.level for item in permissions}


def _levels(folder, roles, indexed) -> dict[str, str]:
    if folder is None:
        return {}
    return {
        role.name: indexed[(folder.id, role.id)]
        for role in roles
        if (folder.id, role.id) in indexed
    }


def _status_from_diffs(diffs: list[CompareDiff]) -> str:
    kinds = {item.kind for item in diffs}
    if "permission_mismatch" in kinds:
        return "permission_mismatch"
    if "role_missing" in kinds:
        return "role_missing"
    return "same"
