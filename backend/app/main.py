import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.database import Base, get_engine, get_session, init_db
from app.routers import demo, memberships, permissions, projects
from app.schemas import HealthOut
from app.seed import ensure_seed


def create_app(
    database_url: str | None = None,
    cors_origins: str | None = None,
    seed_on_startup: bool | None = None,
    simulate_latency_ms: int | None = None,
) -> FastAPI:
    settings = Settings()
    updates = {}
    if database_url is not None:
        updates["database_url"] = database_url
    if cors_origins is not None:
        updates["cors_origins"] = cors_origins
    if seed_on_startup is not None:
        updates["seed_on_startup"] = seed_on_startup
    if simulate_latency_ms is not None:
        updates["simulate_latency_ms"] = simulate_latency_ms
    if updates:
        settings = settings.model_copy(update=updates)

    init_db(settings.resolved_database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        Base.metadata.create_all(bind=get_engine())
        if _app.state.seed_on_startup:
            db = get_session()
            try:
                ensure_seed(db)
            finally:
                db.close()
        yield

    app = FastAPI(
        title="Senda API",
        description=(
            "API de demostración para administrar usuarios y permisos de carpetas en obras. "
            "Todos los datos son ficticios y no se conecta a ningún servicio externo."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.seed_on_startup = settings.seed_on_startup
    app.state.simulate_latency_ms = settings.simulate_latency_ms

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    @app.middleware("http")
    async def simulate_latency(request, call_next):
        delay = getattr(request.app.state, "simulate_latency_ms", 0)
        if delay > 0:
            await asyncio.sleep(delay / 1000)
        return await call_next(request)

    app.include_router(projects.router)
    app.include_router(memberships.router)
    app.include_router(permissions.router)
    app.include_router(demo.router)

    @app.get("/api/health", response_model=HealthOut, tags=["health"])
    def health():
        return HealthOut(status="ok", database=get_engine().dialect.name)

    return app


app = create_app()
