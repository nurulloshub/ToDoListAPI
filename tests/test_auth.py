import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    r = await client.post(
        "/register",
        json={"name": "John", "email": "john@doe.com", "password": "password1"},
    )
    assert r.status_code == 201
    body = r.json()
    assert "token" in body and body["access_token"]

    r = await client.post(
        "/login", json={"email": "john@doe.com", "password": "password1"}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client):
    payload = {"name": "A", "email": "a@b.com", "password": "secret1"}
    assert (await client.post("/register", json=payload)).status_code == 201
    r = await client.post("/register", json=payload)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_bad_login(client):
    await client.post(
        "/register",
        json={"name": "X", "email": "x@y.com", "password": "secret1"},
    )
    r = await client.post("/login", json={"email": "x@y.com", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    r = await client.post(
        "/register",
        json={"name": "R", "email": "r@r.com", "password": "secret1"},
    )
    refresh = r.json()["refresh_token"]
    r = await client.post("/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert r.json()["access_token"]