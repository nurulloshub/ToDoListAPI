import pytest


async def _auth_headers(client, email="u@u.com"):
    r = await client.post(
        "/register", json={"name": "U", "email": email, "password": "secret1"}
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_unauthorized(client):
    assert (await client.get("/todos")).status_code == 401


@pytest.mark.asyncio
async def test_crud_flow(client):
    headers = await _auth_headers(client)

    r = await client.post(
        "/todos",
        json={"title": "Buy groceries", "description": "Milk, eggs, bread"},
        headers=headers,
    )
    assert r.status_code == 201
    todo_id = r.json()["id"]

    r = await client.put(
        f"/todos/{todo_id}",
        json={"title": "Buy groceries", "description": "Milk, eggs, bread, cheese"},
        headers=headers,
    )
    assert r.status_code == 200
    assert "cheese" in r.json()["description"]

    r = await client.get("/todos", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1 and body["page"] == 1 and body["limit"] == 10

    r = await client.delete(f"/todos/{todo_id}", headers=headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_forbidden_on_other_users_todo(client):
    owner = await _auth_headers(client, "owner@x.com")
    other = await _auth_headers(client, "other@x.com")

    r = await client.post("/todos", json={"title": "Private"}, headers=owner)
    todo_id = r.json()["id"]

    r = await client.put(f"/todos/{todo_id}", json={"title": "hacked"}, headers=other)
    assert r.status_code == 403

    r = await client.delete(f"/todos/{todo_id}", headers=other)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_filter_sort_paginate(client):
    headers = await _auth_headers(client, "p@p.com")
    for i in range(5):
        await client.post(
            "/todos", json={"title": f"task-{i}", "completed": i % 2 == 0}, headers=headers
        )

    r = await client.get("/todos?completed=true", headers=headers)
    assert r.json()["total"] == 3

    r = await client.get("/todos?sort_by=title&order=asc&page=1&limit=2", headers=headers)
    body = r.json()
    assert [t["title"] for t in body["data"]] == ["task-0", "task-1"]