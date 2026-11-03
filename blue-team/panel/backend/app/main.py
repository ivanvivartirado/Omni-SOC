import logging
import secrets
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from app.api import auth, dashboard, users, ws
from app.connectors.registry import build_connectors
from app.core.config import Settings, get_settings
from app.core.db import create_all, init_engine, session_factory
from app.core.security import CSRF_COOKIE, CSRF_HEADER, hash_password
from app.demo.world import DemoWorld
from app.models import Role, User
from app.services.event_bus import EventBus
from app.services.manager import ConnectorManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("panel")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_EXEMPT = {"/api/auth/login"}


async def ensure_admin(settings: Settings) -> None:
    async with session_factory()() as s:
        if await s.scalar(select(func.count()).select_from(User).where(User.role == Role.ADMIN)):
            return
        password = settings.admin_password
        if not password:
            password = secrets.token_urlsafe(16)
            log.warning("=" * 60)
            log.warning("Usuario inicial '%s' creado con contraseña: %s", settings.admin_username, password)
            log.warning("Cámbiala tras el primer acceso. No se volverá a mostrar.")
            log.warning("=" * 60)
        s.add(
            User(
                username=settings.admin_username.lower(),
                full_name="Administrador",
                role=Role.ADMIN,
                password_hash=hash_password(password),
            )
        )
        await s.commit()


def create_app(settings: Settings | None = None, start_manager: bool = True) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        init_engine(settings.db_url)
        await create_all()
        await ensure_admin(settings)
        world = DemoWorld(thresholds=settings.wazuh_levels) if settings.demo_mode else None
        bus = EventBus()
        manager = ConnectorManager(settings, build_connectors(settings, world), bus, world)
        app.state.settings, app.state.bus, app.state.manager = settings, bus, manager
        if start_manager:
            await manager.start()
        log.info("Panel iniciado (modo %s)", "DEMO" if settings.demo_mode else "real")
        yield
        await manager.stop()

    app = FastAPI(
        title="Omni SOC · Blue Team Command Center",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.demo_mode else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.demo_mode else None,
    )

    @app.middleware("http")
    async def security_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in UNSAFE_METHODS and request.url.path not in CSRF_EXEMPT:
            cookie = request.cookies.get(CSRF_COOKIE)
            header = request.headers.get(CSRF_HEADER)
            if not cookie or not header or not secrets.compare_digest(cookie, header):
                return JSONResponse({"detail": "Token CSRF inválido"}, status_code=403)
            origin = request.headers.get("origin")
            if origin and origin not in settings.origins:
                return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            if k == "Content-Security-Policy" and request.url.path.startswith("/api/docs"):
                continue
            response.headers.setdefault(k, v)
        return response

    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(users.router)
    app.include_router(ws.router)

    @app.get("/api/health")
    async def health() -> dict[str, object]:
        return {"status": "ok", "demo_mode": settings.demo_mode}

    return app


app = create_app()
