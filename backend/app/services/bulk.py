from app.providers.base import ProjectProvider
from app.schemas import MembershipBulkResult, MembershipInput, MembershipPlanRow

SIMULATED_FAILURE_EMAIL = "falla@demo.example"


def plan_memberships(provider: ProjectProvider, rows: list[MembershipInput]) -> list[MembershipPlanRow]:
    planned: list[MembershipPlanRow] = []
    for line, row in enumerate(rows, start=1):
        planned.extend(_classify_row(provider, line, row))
    return planned


def preview_memberships(provider: ProjectProvider, rows: list[MembershipInput]) -> MembershipBulkResult:
    return _summarize(plan_memberships(provider, rows))


def apply_memberships(provider: ProjectProvider, rows: list[MembershipInput]) -> MembershipBulkResult:
    planned = plan_memberships(provider, rows)
    applied = 0
    for item in planned:
        if item.status not in {"applicable", "update_role"}:
            continue
        user = provider.get_user_by_email(item.email)
        if user is None:
            user = provider.create_user(item.name, item.email, item.company)
        project = provider.get_project_by_name_or_code(item.project)
        role = provider.get_role_by_name(item.role)
        membership = provider.get_membership(user.id, project.id)
        if item.status == "update_role" and membership is not None:
            provider.update_membership_role(membership, role.id)
            applied += 1
            continue
        if membership is not None:
            item.status = "already_member"
            item.message = "Ya tiene un rol en este proyecto. La fila duplicada no se volvió a aplicar."
            continue
        provider.add_membership(user.id, project.id, role.id)
        applied += 1

    summary = _count(planned)
    provider.add_audit(
        "bulk_memberships",
        {
            "mensaje": "Asignación masiva de usuarios.",
            "aplicadas": applied,
            "omitidas": summary["already_member"],
            "rechazadas": summary["rejected"],
            "filas": [item.model_dump() for item in planned],
        },
    )
    provider.commit()
    summary["applied"] = applied
    return MembershipBulkResult(rows=planned, summary=summary)


def _classify_row(provider: ProjectProvider, line: int, row: MembershipInput) -> list[MembershipPlanRow]:
    name = row.name.strip()
    email = row.email.strip().lower()
    company = row.company.strip()
    role_name = row.role.strip()
    projects = [part.strip() for part in row.projects.split(";") if part.strip()]

    def one(status: str, message: str, project: str = "") -> MembershipPlanRow:
        return MembershipPlanRow(
            line=line,
            name=name,
            email=email,
            company=company,
            role=role_name,
            project=project,
            status=status,
            message=message,
        )

    if email == SIMULATED_FAILURE_EMAIL:
        return [one("simulated_error", "El proveedor simulado rechazó este correo a propósito.")]
    if not name or not email or not role_name or not projects:
        return [one("incomplete", "Faltan nombre, correo, rol o proyecto.")]
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        return [one("invalid_email", "El correo no es válido.")]

    role = provider.get_role_by_name(role_name)
    if role is None:
        return [one("unknown_role", f"El rol «{role_name}» no existe.")]

    classified = []
    for project_name in projects:
        project = provider.get_project_by_name_or_code(project_name)
        if project is None:
            classified.append(one("unknown_project", f"No hay un proyecto llamado «{project_name}».", project_name))
            continue
        user = provider.get_user_by_email(email)
        if user is None:
            classified.append(
                one(
                    "applicable",
                    f"Se creará a {name} y se asignará a {project.name} como {role.name}.",
                    project.name,
                )
            )
            continue
        membership = provider.get_membership(user.id, project.id)
        if membership is None:
            classified.append(
                one(
                    "applicable",
                    f"Se asignará a {project.name} como {role.name}.",
                    project.name,
                )
            )
        elif membership.role_id == role.id:
            classified.append(
                one(
                    "already_member",
                    f"Ya es {role.name} en {project.name}.",
                    project.name,
                )
            )
        else:
            classified.append(
                one(
                    "update_role",
                    f"En {project.name} el rol pasará de {membership.role.name} a {role.name}.",
                    project.name,
                )
            )
    return classified


def _summarize(rows: list[MembershipPlanRow]) -> MembershipBulkResult:
    return MembershipBulkResult(rows=rows, summary=_count(rows))


def _count(rows: list[MembershipPlanRow]) -> dict[str, int]:
    rejected = {"incomplete", "invalid_email", "unknown_role", "unknown_project", "simulated_error"}
    return {
        "total": len(rows),
        "applicable": sum(row.status == "applicable" for row in rows),
        "update_role": sum(row.status == "update_role" for row in rows),
        "already_member": sum(row.status == "already_member" for row in rows),
        "rejected": sum(row.status in rejected for row in rows),
    }

