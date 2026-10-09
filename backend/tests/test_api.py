import pytest
from fastapi.testclient import TestClient

from app.config import normalize_database_url
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    database = tmp_path / "test.db"
    application = create_app(
        database_url=f"sqlite:///{database.as_posix()}",
        cors_origins="http://localhost:3000",
        seed_on_startup=True,
        simulate_latency_ms=0,
    )
    with TestClient(application) as test_client:
        yield test_client


def _row(path: str, result: dict) -> dict:
    return next(item for item in result["rows"] if item["path"] == path)


def test_normalize_database_url():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url("sqlite:///./data/demo.db") == "sqlite:///./data/demo.db"


def test_health_and_seeded_projects(client: TestClient):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["database"] == "sqlite"

    projects = client.get("/api/projects")
    assert projects.status_code == 200
    codes = {item["code"] for item in projects.json()}
    assert codes == {"TORRE-1", "TORRE-2", "PUENTE-1"}


def test_compare_known_differences(client: TestClient):
    response = client.get("/api/compare", params={"a": "torre-1", "b": "torre-2"})
    assert response.status_code == 200
    body = response.json()

    planos = _row("03 Construcción/Planos", body)
    assert planos["status"] == "permission_mismatch"
    contratista = next(item for item in planos["diffs"] if item["role"] == "Contratista")
    assert contratista["level_a"] == "editar"
    assert contratista["level_b"] == "ver"

    mep = _row("02 Diseño/MEP", body)
    assert mep["status"] == "permission_mismatch"
    visor = next(item for item in mep["diffs"] if item["role"] == "Visor")
    assert visor["level_a"] == "descargar"
    assert visor["level_b"] == "ver"

    ensayos = _row("04 Calidad/Ensayos", body)
    assert ensayos["status"] == "role_missing"
    residente = next(item for item in ensayos["diffs"] if item["role"] == "Residente")
    assert residente["level_a"] == "editar"
    assert residente["level_b"] is None

    incidentes = _row("05 Seguridad/Incidentes", body)
    assert incidentes["status"] == "missing_in_b"
    assert body["summary"]["missing_in_b"] == 1
    assert body["summary"]["permission_mismatch"] == 2
    assert body["summary"]["role_missing"] == 1


def test_compare_same_project_has_no_differences(client: TestClient):
    response = client.get("/api/compare", params={"a": "torre-1", "b": "torre-1"})
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["same"] == summary["total"]
    assert summary["permission_mismatch"] == 0
    assert summary["missing_in_a"] == 0


def test_compare_missing_project_returns_404(client: TestClient):
    response = client.get("/api/compare", params={"a": "torre-1", "b": "no-existe"})
    assert response.status_code == 404


def test_preview_does_not_persist_and_classifies_rows(client: TestClient):
    before = client.get("/api/projects/torre-1").json()["member_count"]
    payload = {
        "rows": [
            {
                "name": "Marta Peña",
                "email": "marta.pena@andina.example",
                "company": "Constructora Andina",
                "role": "Contratista",
                "projects": "TORRE-1",
            },
            {
                "name": "Luis Gómez",
                "email": "luis.gomez@andina.example",
                "company": "Constructora Andina",
                "role": "Visor",
                "projects": "TORRE-1",
            },
            {
                "name": "Elena Vargas",
                "email": "elena.vargas@concretos.example",
                "company": "Concretos del Valle",
                "role": "Contratista",
                "projects": "TORRE-1; TORRE-2",
            },
            {
                "name": "Pedro Falla",
                "email": "falla@demo.example",
                "company": "Simulación Demo",
                "role": "Visor",
                "projects": "TORRE-1",
            },
            {
                "name": "Nadine Ruiz",
                "email": "nadine.ruiz@concretos.example",
                "company": "Concretos del Valle",
                "role": "Gerente",
                "projects": "TORRE-1",
            },
            {
                "name": "Olga Marín",
                "email": "olga.marin@concretos.example",
                "company": "Concretos del Valle",
                "role": "Contratista",
                "projects": "Obra Fantasma",
            },
        ]
    }
    preview = client.post("/api/memberships/bulk/preview", json=payload)
    assert preview.status_code == 200
    summary = preview.json()["summary"]
    assert summary["already_member"] == 1
    assert summary["update_role"] == 1
    assert summary["applicable"] == 2
    assert summary["rejected"] == 3
    assert client.get("/api/projects/torre-1").json()["member_count"] == before


def test_apply_partial_batch_and_audit(client: TestClient):
    payload = {
        "rows": [
            {
                "name": "Elena Vargas",
                "email": "elena.vargas@concretos.example",
                "company": "Concretos del Valle",
                "role": "Contratista",
                "projects": "TORRE-1; PUENTE-1",
            },
            {
                "name": "Nadine Ruiz",
                "email": "nadine.ruiz@concretos.example",
                "company": "Concretos del Valle",
                "role": "Gerente",
                "projects": "TORRE-1",
            },
        ]
    }
    applied = client.post("/api/memberships/bulk/apply", json=payload)
    assert applied.status_code == 200
    body = applied.json()
    assert body["summary"]["applied"] == 2
    assert body["summary"]["rejected"] == 1

    members = client.get("/api/projects/torre-1").json()["members"]
    elena = next(item for item in members if item["email"] == "elena.vargas@concretos.example")
    assert elena["role"] == "Contratista"
    puente = client.get("/api/projects/puente-1").json()["members"]
    assert any(item["email"] == "elena.vargas@concretos.example" for item in puente)

    audit = client.get("/api/audit").json()
    assert audit[0]["action"] == "bulk_memberships"
    assert audit[0]["detail"]["aplicadas"] == 2
    assert audit[0]["detail"]["rechazadas"] == 1


def test_duplicate_row_in_one_batch_is_not_applied_twice(client: TestClient):
    row = {
        "name": "Helena Patiño",
        "email": "helena.patino@andina.example",
        "company": "Constructora Andina",
        "role": "Residente",
        "projects": "TORRE-2",
    }
    applied = client.post("/api/memberships/bulk/apply", json={"rows": [row, row]})
    assert applied.status_code == 200
    statuses = [item["status"] for item in applied.json()["rows"]]
    assert statuses.count("applicable") == 1
    assert statuses.count("already_member") == 1
    members = client.get("/api/projects/torre-2").json()["members"]
    assert sum(item["email"] == "helena.patino@andina.example" for item in members) == 1


def test_permission_preview_and_apply(client: TestClient):
    matrix = client.get("/api/projects/torre-1/permissions").json()
    folder = next(item for item in matrix["folders"] if item["path"] == "03 Construcción/Informes")
    role = next(item for item in matrix["roles"] if item["name"] == "Visor")
    payload = {
        "project_id": "torre-1",
        "folder_ids": [folder["id"], "carpeta-ajena"],
        "role_id": role["id"],
        "level": "editar",
    }
    preview = client.post("/api/permissions/bulk/preview", json=payload)
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["summary"]["change"] == 1
    assert preview_body["summary"]["rejected"] == 1
    assert folder["permissions"][role["id"]] == "ver"

    applied = client.post("/api/permissions/bulk/apply", json=payload)
    assert applied.status_code == 200
    assert applied.json()["summary"]["applied"] == 1

    refreshed = client.get("/api/projects/torre-1/permissions").json()
    updated = next(item for item in refreshed["folders"] if item["id"] == folder["id"])
    assert updated["permissions"][role["id"]] == "editar"


def test_export_csv_includes_bom_and_folder_path(client: TestClient):
    response = client.get("/api/projects/torre-1/permissions/export")
    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    text = response.content.decode("utf-8-sig")
    assert "Ruta,Coordinador,Residente,Contratista,Visor" in text
    assert "03 Construcción/Planos" in text

    workbook = client.get("/api/projects/torre-1/permissions/export", params={"format": "xlsx"})
    assert workbook.status_code == 200
    assert workbook.content[:2] == b"PK"


def test_metadata_download_and_reset(client: TestClient):
    metadata = client.get("/api/projects/puente-1/metadata")
    assert metadata.status_code == 200
    assert "attachment" in metadata.headers["content-disposition"]
    assert "Concesión Vial del Cañón" in metadata.json()["proyecto"]["client"]

    created = client.post(
        "/api/memberships/bulk/apply",
        json={
            "rows": [
                {
                    "name": "Renata Vidal",
                    "email": "renata.vidal@loscerros.example",
                    "company": "Inmobiliaria Los Cerros",
                    "role": "Visor",
                    "projects": "PUENTE-1",
                }
            ]
        },
    )
    assert created.status_code == 200
    reset = client.post("/api/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["projects"] == 3
    members = client.get("/api/projects/puente-1").json()["members"]
    assert all(item["email"] != "renata.vidal@loscerros.example" for item in members)
    assert any(item["email"] == "ana.rios@loscerros.example" for item in members)
