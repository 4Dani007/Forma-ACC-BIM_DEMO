"""Datos ficticios de obras, personas y permisos.

Las diferencias entre Torre Andina etapa 1 y etapa 2 están sembradas
a propósito para que el comparador tenga casos conocidos.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog, Folder, FolderPermission, Membership, Project, Role, User

ROLES = [
    ("coordinador", "Coordinador", 1),
    ("residente", "Residente", 2),
    ("contratista", "Contratista", 3),
    ("visor", "Visor", 4),
]

PROJECTS = [
    {
        "id": "torre-1",
        "name": "Torre Andina - Etapa 1",
        "code": "TORRE-1",
        "status": "En obra",
        "location": "Bogotá",
        "client": "Inmobiliaria Los Cerros",
        "phase": "Estructura",
        "created_at": datetime(2025, 3, 12, tzinfo=timezone.utc),
    },
    {
        "id": "torre-2",
        "name": "Torre Andina - Etapa 2",
        "code": "TORRE-2",
        "status": "En obra",
        "location": "Bogotá",
        "client": "Inmobiliaria Los Cerros",
        "phase": "Cimentación",
        "created_at": datetime(2025, 11, 3, tzinfo=timezone.utc),
    },
    {
        "id": "puente-1",
        "name": "Puente del Río Claro",
        "code": "PUENTE-1",
        "status": "En diseño",
        "location": "Antioquia",
        "client": "Concesión Vial del Cañón",
        "phase": "Estudios",
        "created_at": datetime(2026, 1, 20, tzinfo=timezone.utc),
    },
]

TREE_TORRE = {
    "01 Contractual": ["Contratos", "Actas"],
    "02 Diseño": ["Arquitectura", "Estructura", "MEP"],
    "03 Construcción": ["Planos", "Programación", "Informes"],
    "04 Calidad": ["Ensayos", "No conformidades"],
    "05 Seguridad": ["Procedimientos", "Incidentes"],
}

TREE_PUENTE = {
    "01 Contractual": ["Contratos"],
    "02 Ingeniería": ["Topografía", "Estructural"],
    "03 Obra": ["Fundaciones", "Superestructura"],
    "04 Ambiental": ["Permisos"],
    "05 Seguridad": ["Procedimientos"],
}

SKIP_PATHS = {
    "torre-2": {"05 Seguridad/Incidentes"},
}

USERS = [
    ("u-ana-rios", "Ana Ríos", "ana.rios@loscerros.example", "Inmobiliaria Los Cerros"),
    ("u-luis-gomez", "Luis Gómez", "luis.gomez@andina.example", "Constructora Andina"),
    ("u-marta-pena", "Marta Peña", "marta.pena@andina.example", "Constructora Andina"),
    ("u-julian-ortiz", "Julián Ortiz", "julian.ortiz@nova.example", "Estructura Nova"),
    ("u-camila-duarte", "Camila Duarte", "camila.duarte@alto.example", "Seguridad Alto"),
    ("u-hector-salas", "Héctor Salas", "hector.salas@rioclaro.example", "Consorcio Río Claro"),
    ("u-diana-cruz", "Diana Cruz", "diana.cruz@rioclaro.example", "Consorcio Río Claro"),
    ("u-sofia-beltran", "Sofía Beltrán", "sofia.beltran@mepcentro.example", "MEP del Centro"),
]

MEMBERSHIPS = [
    ("u-ana-rios", "torre-1", "coordinador"),
    ("u-ana-rios", "torre-2", "coordinador"),
    ("u-ana-rios", "puente-1", "coordinador"),
    ("u-luis-gomez", "torre-1", "residente"),
    ("u-luis-gomez", "torre-2", "residente"),
    ("u-marta-pena", "torre-1", "contratista"),
    ("u-julian-ortiz", "torre-1", "contratista"),
    ("u-camila-duarte", "torre-1", "visor"),
    ("u-camila-duarte", "puente-1", "visor"),
    ("u-hector-salas", "puente-1", "residente"),
    ("u-diana-cruz", "puente-1", "coordinador"),
    ("u-sofia-beltran", "torre-2", "visor"),
]


def tower_level(path: str, role: str) -> str | None:
    top = path.split("/")[0]
    if role == "Coordinador":
        return "administrar"
    if role == "Visor":
        if path.startswith("02 Diseño"):
            return "descargar"
        return "ver"
    if role == "Residente":
        if top in {"03 Construcción", "04 Calidad"}:
            return "editar"
        if top == "02 Diseño":
            return "descargar"
        return "ver"
    if role == "Contratista":
        if path in {"03 Construcción/Planos", "03 Construcción/Programación"}:
            return "editar"
        if top == "03 Construcción":
            return "descargar"
        return "ver"
    return None


def torre2_level(path: str, role: str) -> str | None:
    if path == "03 Construcción/Planos" and role == "Contratista":
        return "ver"
    if path == "02 Diseño/MEP" and role == "Visor":
        return "ver"
    if path == "04 Calidad/Ensayos" and role == "Residente":
        return None
    return tower_level(path, role)


def puente_level(path: str, role: str) -> str | None:
    top = path.split("/")[0]
    if role == "Coordinador":
        return "administrar"
    if role == "Residente":
        return "editar" if top == "03 Obra" else "ver"
    if role == "Contratista":
        if top == "03 Obra":
            return "descargar"
        if top == "02 Ingeniería":
            return "ver"
        return "ver"
    if role == "Visor":
        return "ver"
    return None


LEVEL_FOR = {
    "torre-1": tower_level,
    "torre-2": torre2_level,
    "puente-1": puente_level,
}

TREE_FOR = {
    "torre-1": TREE_TORRE,
    "torre-2": TREE_TORRE,
    "puente-1": TREE_PUENTE,
}


def _add_tree(db: Session, project_id: str, roles: list[Role]) -> tuple[int, int]:
    tree = TREE_FOR[project_id]
    skip = SKIP_PATHS.get(project_id, set())
    level_for = LEVEL_FOR[project_id]
    role_by_name = {role.name: role for role in roles}
    position = 0
    folders = 0
    permissions = 0

    for root, children in tree.items():
        parent = Folder(
            id=f"{project_id}-f{position}",
            project_id=project_id,
            parent_id=None,
            name=root,
            path=root,
            depth=0,
            position=position,
        )
        position += 1
        db.add(parent)
        folders += 1
        created = [parent]
        for child in children:
            path = f"{root}/{child}"
            if path in skip:
                continue
            folder = Folder(
                id=f"{project_id}-f{position}",
                project_id=project_id,
                parent_id=parent.id,
                name=child,
                path=path,
                depth=1,
                position=position,
            )
            position += 1
            db.add(folder)
            folders += 1
            created.append(folder)

        for folder in created:
            for role_name, role in role_by_name.items():
                level = level_for(folder.path, role_name)
                if not level:
                    continue
                db.add(
                    FolderPermission(
                        id=f"perm-{folder.id}-{role.id}",
                        folder_id=folder.id,
                        role_id=role.id,
                        level=level,
                    )
                )
                permissions += 1

    return folders, permissions


def seed(db: Session) -> dict[str, int]:
    roles = [Role(id=role_id, name=name, position=position) for role_id, name, position in ROLES]
    db.add_all(roles)
    db.add_all(Project(**project) for project in PROJECTS)
    db.add_all(User(id=uid, name=name, email=email, company=company) for uid, name, email, company in USERS)

    folders = 0
    permissions = 0
    for project in PROJECTS:
        folder_count, permission_count = _add_tree(db, project["id"], roles)
        folders += folder_count
        permissions += permission_count

    for user_id, project_id, role_id in MEMBERSHIPS:
        db.add(
            Membership(
                id=f"m-{user_id}-{project_id}",
                user_id=user_id,
                project_id=project_id,
                role_id=role_id,
            )
        )

    db.add(
        AuditLog(
            id="audit-seed",
            action="seed",
            actor="Sistema",
            detail={"mensaje": "Se cargaron los datos de ejemplo de la demostración."},
            created_at=datetime.now(timezone.utc),
        )
    )
    db.flush()
    return {
        "projects": len(PROJECTS),
        "users": len(USERS),
        "folders": folders,
        "memberships": len(MEMBERSHIPS),
        "permissions": permissions,
    }


def ensure_seed(db: Session) -> None:
    count = db.scalar(select(func.count()).select_from(Project)) or 0
    if count == 0:
        seed(db)
        db.commit()


def reset_database(db: Session) -> dict[str, int]:
    from sqlalchemy import update

    from app.database import Base

    db.execute(update(Folder).values(parent_id=None))
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    counts = seed(db)
    db.commit()
    return counts
