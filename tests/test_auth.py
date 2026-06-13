import pytest


async def test_register_success(client):
    response = await client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_without_full_name(client):
    response = await client.post("/auth/register", json={
        "email": "nofullname@example.com",
        "password": "password123",
    })
    assert response.status_code == 201
    assert response.json()["full_name"] is None


async def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_invalid_email(client):
    response = await client.post("/auth/register", json={
        "email": "notanemail",
        "password": "password123",
    })
    assert response.status_code == 422


async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "password123",
    })
    response = await client.post("/auth/login", data={
        "username": "login@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "correctpassword",
    })
    response = await client.post("/auth/login", data={
        "username": "wrongpass@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


async def test_login_unknown_email(client):
    response = await client.post("/auth/login", data={
        "username": "nobody@example.com",
        "password": "password123",
    })
    assert response.status_code == 401


async def test_protected_route_without_token(client):
    response = await client.get("/applications")
    assert response.status_code == 401


async def test_protected_route_with_invalid_token(client):
    response = await client.get(
        "/applications",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


async def test_me_returns_current_user(client, auth_headers):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "user"
    assert "id" in data
    assert "hashed_password" not in data


async def test_me_without_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_with_invalid_token(client):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
