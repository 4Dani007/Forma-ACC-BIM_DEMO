from abc import ABC, abstractmethod

from app.models import AuditLog, Folder, FolderPermission, Membership, Project, Role, User


class ProjectProvider(ABC):
    """Fuente de proyectos, carpetas y permisos.

    La lógica de negocio habla con esta interfaz. La demo usa una
    implementación con datos ficticios; otra implementación podría
    hablar con una API externa sin cambiar los servicios.
    """

    @abstractmethod
    def list_projects(self) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    def get_project(self, project_id: str) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    def get_project_by_name_or_code(self, value: str) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    def list_roles(self) -> list[Role]:
        raise NotImplementedError

    @abstractmethod
    def get_role(self, role_id: str) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    def get_role_by_name(self, name: str) -> Role | None:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def create_user(self, name: str, email: str, company: str) -> User:
        raise NotImplementedError

    @abstractmethod
    def list_folders(self, project_id: str) -> list[Folder]:
        raise NotImplementedError

    @abstractmethod
    def list_memberships(self, project_id: str) -> list[Membership]:
        raise NotImplementedError

    @abstractmethod
    def get_membership(self, user_id: str, project_id: str) -> Membership | None:
        raise NotImplementedError

    @abstractmethod
    def add_membership(self, user_id: str, project_id: str, role_id: str) -> Membership:
        raise NotImplementedError

    @abstractmethod
    def update_membership_role(self, membership: Membership, role_id: str) -> Membership:
        raise NotImplementedError

    @abstractmethod
    def list_permissions(self, project_id: str) -> list[FolderPermission]:
        raise NotImplementedError

    @abstractmethod
    def get_permission(self, folder_id: str, role_id: str) -> FolderPermission | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_permission(self, folder_id: str, role_id: str, level: str) -> FolderPermission:
        raise NotImplementedError

    @abstractmethod
    def add_audit(self, action: str, detail: dict, actor: str = "Demostración") -> AuditLog:
        raise NotImplementedError

    @abstractmethod
    def list_audit(self, limit: int = 100) -> list[AuditLog]:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError
