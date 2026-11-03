import pytest

from tests.conftest import csrf, login


async def test_health_and_security_headers(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.headers["x-frame-options"] == "DENY"


async def test_protected_routes_require_auth(client):
    assert (await client.get("/api/dashboard/summary")).status_code == 401
    assert (await client.get("/api/alerts")).status_code == 401


async def test_login_sets_httponly_cookies_and_me(client):
    r = await login(client)
    assert r.status_code == 200 and r.json()["role"] == "admin"
    set_cookie = " ".join(r.headers.get_list("set-cookie"))
    assert "access_token=" in set_cookie and "HttpOnly" in set_cookie and "SameSite=strict" in set_cookie
    assert (await client.get("/api/auth/me")).json()["username"] == "admin"


async def test_bad_password_then_lockout(client):
    for _ in range(3):
        assert (await login(client, password="wrong")).status_code == 401
    r = await login(client)
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0


async def test_csrf_required_for_unsafe_methods(client):
    await login(client)
    assert (await client.post("/api/auth/logout")).status_code == 403
    assert (await client.post("/api/auth/logout", headers=csrf(client))).status_code == 200
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_logout_invalidates_old_tokens(client):
    await login(client)
    old = client.cookies.get("access_token")
    await client.post("/api/auth/logout", headers=csrf(client))
    client.cookies.set("access_token", old)
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_rbac_and_audit(client):
    await login(client)
    r = await client.post(
        "/api/users", headers=csrf(client), json={"username": "lector", "password": "Lector-Pass-123", "role": "viewer"}
    )
    assert r.status_code == 201
    weak = await client.post(
        "/api/users", headers=csrf(client), json={"username": "debil", "password": "aaaaaaaaaaaa", "role": "viewer"}
    )
    assert weak.status_code == 422
    audit = (await client.get("/api/audit")).json()
    assert {"login_success", "user_created"} <= {i["action"] for i in audit["items"]}

    client.cookies.clear()
    await login(client, "lector", "Lector-Pass-123")
    assert (await client.get("/api/audit")).status_code == 403
    assert (await client.post("/api/demo/trigger/eicar", headers=csrf(client))).status_code == 403


@pytest.mark.parametrize("rng", ["24h", "7d"])
async def test_dashboard_summary_shape(client, rng):
    await login(client)
    m = client._transport.app.state.manager  # type: ignore[attr-defined]
    await m._seed_demo_history()
    for c in m.connectors:
        m.state[c.name] = await c.collect_state()
    r = await client.get(f"/api/dashboard/summary?range={rng}")
    assert r.status_code == 200
    data = r.json()
    assert data["kpis"]["agents"] == {"active": 3, "total": 4, "pct": 75.0}
    assert 0 <= data["score"]["total"] <= 100
    assert data["charts"]["timeline"] and data["charts"]["top_rules"]
    assert data["dhcp"][0]["size"] == 31
    alerts = (await client.get("/api/alerts?min_severity=3&limit=5")).json()
    assert alerts["total"] > 0 and all(a["severity"] >= 3 for a in alerts["items"])
