from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["ver", "descargar", "editar", "administrar"]


class ProjectOut(BaseModel):
    id: str
    name: str
    code: str
    status: str
    location: str
    client: str
    phase: str
    created_at: datetime
    folder_count: int
    member_count: int


class MemberOut(BaseModel):
    user_id: str
    name: str
    email: str
    company: str
    role_id: str
    role: str


class ProjectDetail(ProjectOut):
    members: list[MemberOut]


class RoleOut(BaseModel):
    id: str
    name: str


class ProjectRef(BaseModel):
    id: str
    name: str
    code: str


class FolderRow(BaseModel):
    id: str
    name: str
    path: str
    depth: int
    parent_id: str | None
    permissions: dict[str, str]


class PermissionsMatrix(BaseModel):
    project: ProjectRef
    roles: list[RoleOut]
    folders: list[FolderRow]


class MembershipInput(BaseModel):
    name: str = ""
    email: str = ""
    company: str = ""
    role: str = ""
    projects: str = ""


class MembershipBulkRequest(BaseModel):
    rows: list[MembershipInput] = Field(min_length=1, max_length=500)


class MembershipPlanRow(BaseModel):
    line: int
    name: str
    email: str
    company: str
    role: str
    project: str
    status: str
    message: str


class MembershipBulkResult(BaseModel):
    rows: list[MembershipPlanRow]
    summary: dict[str, int]


class PermissionBulkRequest(BaseModel):
    project_id: str
    folder_ids: list[str] = Field(min_length=1, max_length=500)
    role_id: str
    level: Level


class PermissionPlanRow(BaseModel):
    folder_id: str
    path: str
    role: str
    level_before: str | None
    level_after: str | None
    status: str
    message: str


class PermissionBulkResult(BaseModel):
    rows: list[PermissionPlanRow]
    summary: dict[str, int]


class CompareDiff(BaseModel):
    role: str
    level_a: str | None
    level_b: str | None
    kind: str


class CompareRow(BaseModel):
    path: str
    name: str
    depth: int
    status: str
    permissions_a: dict[str, str]
    permissions_b: dict[str, str]
    diffs: list[CompareDiff]


class CompareSummary(BaseModel):
    total: int
    same: int
    permission_mismatch: int
    role_missing: int
    missing_in_a: int
    missing_in_b: int


class CompareResult(BaseModel):
    project_a: ProjectRef
    project_b: ProjectRef
    summary: CompareSummary
    rows: list[CompareRow]


class AuditOut(BaseModel):
    id: str
    action: str
    actor: str
    detail: dict
    created_at: datetime


class HealthOut(BaseModel):
    status: str
    database: str


class ResetOut(BaseModel):
    projects: int
    users: int
    folders: int
    memberships: int
    permissions: int
