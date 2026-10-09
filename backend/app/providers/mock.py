from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import AuditLog, Folder, FolderPermission, Membership, Project, Role, User
from app.providers.base import ProjectProvider


def user_id_for(email: str) -> str:
    local = email.split("@")[0].replace(".", "-")
    return f"u-{local}"


class MockProvider(ProjectProvider):
    """Lee y escribe la base de la demo. No llama a ningún servicio externo."""

    def __init__(self, db: Session):
        self.db = db

    def list_projects(self) -> list[Project]:
        return list(self.db.scalars(select(Project).order_by(Project.name)).all())

    def get_project(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)

    def get_project_by_name_or_code(self, value: str) -> Project | None:
        key = value.strip().casefold()
        for project in self.list_projects():
            if project.name.casefold() == key or project.code.casefold() == key:
                return project
        return None

    def list_roles(self) -> list[Role]:
        return list(self.db.scalars(select(Role).order_by(Role.position)).all())

    def get_role(self, role_id: str) -> Role | None:
        return self.db.get(Role, role_id)

    def get_role_by_name(self, name: str) -> Role | None:
        key = name.strip().casefold()
        for role in self.list_roles():
            if role.name.casefold() == key:
                return role
        return None

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.strip().lower()))

    def create_user(self, name: str, email: str, company: str) -> User:
        email = email.strip().lower()
        base = user_id_for(email)
        candidate = base
        suffix = 2
        while self.db.get(User, candidate) is not None:
            candidate = f"{base}-{suffix}"
            suffix += 1
        user = User(id=candidate, name=name.strip(), email=email, company=company.strip())
        self.db.add(user)
        self.db.flush()
        return user

    def list_folders(self, project_id: str) -> list[Folder]:
        return list(
            self.db.scalars(
                select(Folder).where(Folder.project_id == project_id).order_by(Folder.position)
            ).all()
        )

    def list_memberships(self, project_id: str) -> list[Membership]:
        stmt = (
            select(Membership)
            .where(Membership.project_id == project_id)
            .options(selectinload(Membership.user), selectinload(Membership.role))
            .order_by(Membership.id)
        )
        return list(self.db.scalars(stmt).all())

    def get_membership(self, user_id: str, project_id: str) -> Membership | None:
        stmt = (
            select(Membership)
            .where(Membership.user_id == user_id, Membership.project_id == project_id)
            .options(selectinload(Membership.role))
        )
        return self.db.scalar(stmt)

    def add_membership(self, user_id: str, project_id: str, role_id: str) -> Membership:
        membership = Membership(
            id=f"m-{user_id}-{project_id}",
            user_id=user_id,
            project_id=project_id,
            role_id=role_id,
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    def update_membership_role(self, membership: Membership, role_id: str) -> Membership:
        membership.role_id = role_id
        self.db.flush()
        return membership

    def list_permissions(self, project_id: str) -> list[FolderPermission]:
        stmt = (
            select(FolderPermission)
            .join(Folder)
            .where(Folder.project_id == project_id)
            .options(selectinload(FolderPermission.role), selectinload(FolderPermission.folder))
        )
        return list(self.db.scalars(stmt).all())

    def get_permission(self, folder_id: str, role_id: str) -> FolderPermission | None:
        return self.db.scalar(
            select(FolderPermission).where(
                FolderPermission.folder_id == folder_id,
                FolderPermission.role_id == role_id,
            )
        )

    def upsert_permission(self, folder_id: str, role_id: str, level: str) -> FolderPermission:
        current = self.get_permission(folder_id, role_id)
        if current:
            current.level = level
            self.db.flush()
            return current
        created = FolderPermission(
            id=f"perm-{folder_id}-{role_id}",
            folder_id=folder_id,
            role_id=role_id,
            level=level,
        )
        self.db.add(created)
        self.db.flush()
        return created

    def add_audit(self, action: str, detail: dict, actor: str = "Demostración") -> AuditLog:
        entry = AuditLog(
            id=str(uuid4()),
            action=action,
            actor=actor,
            detail=detail,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_audit(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
