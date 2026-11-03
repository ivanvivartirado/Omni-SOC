import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

_tmp = Path(tempfile.mkdtemp(prefix="panel-test-"))
os.environ.setdefault("DATA_DIR", str(_tmp))
os.environ.setdefault("SECRET_KEY", "test-secret-key-" + "x" * 40)
os.environ.setdefault("ADMIN_PASSWORD", "Adm1n-Password!")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ALLOWED_ORIGINS", "http://testserver")

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(data_dir=tmp_path, login_max_failures=3, login_ip_max_failures=50)
    app = create_app(settings, start_manager=False)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
            yield c


async def login(c: httpx.AsyncClient, username: str = "admin", password: str = "Adm1n-Password!") -> httpx.Response:
    return await c.post("/api/auth/login", json={"username": username, "password": password})


def csrf(c: httpx.AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": c.cookies.get("csrf_token", "")}
