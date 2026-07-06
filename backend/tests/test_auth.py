import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    resp = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "test123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "token" in data["data"]

    # Login
    resp = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "test123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    token = data["data"]["token"]

    # Me
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/register",
        json={"email": "test2@example.com", "password": "test123456"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "test2@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401
