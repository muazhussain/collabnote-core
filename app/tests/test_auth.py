from httpx import AsyncClient

_REGISTER_PAYLOAD = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "securepassword123",
}

_LOGIN_PAYLOAD = {
    "username": "alice",
    "password": "securepassword123",
}


async def _register_and_login(client: AsyncClient) -> str:
    await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
    resp = await client.post("/api/v1/auth/login", json=_LOGIN_PAYLOAD)
    return resp.json()["access_token"]


class TestRegister:
    async def test_success(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == _REGISTER_PAYLOAD["email"]
        assert data["username"] == _REGISTER_PAYLOAD["username"]
        assert data["is_active"] is True
        assert "id" in data

    async def test_duplicate_email(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_REGISTER_PAYLOAD, "username": "alice2"},
        )
        assert resp.status_code == 409

    async def test_duplicate_username(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_REGISTER_PAYLOAD, "email": "alice2@example.com"},
        )
        assert resp.status_code == 409


class TestLogin:
    async def test_success(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        resp = await client.post("/api/v1/auth/login", json=_LOGIN_PAYLOAD)
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_wrong_password(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        resp = await client.post(
            "/api/v1/auth/login",
            json={**_LOGIN_PAYLOAD, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_wrong_username(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={**_LOGIN_PAYLOAD, "username": "nonexistent"},
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_success(self, client: AsyncClient) -> None:
        token = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"] != token

    async def test_old_token_revoked_after_refresh(self, client: AsyncClient) -> None:
        token = await _register_and_login(client)
        await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    async def test_invalid_token(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401

    async def test_no_token(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 403


class TestLogout:
    async def test_success(self, client: AsyncClient) -> None:
        token = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    async def test_token_revoked_after_logout(self, client: AsyncClient) -> None:
        token = await _register_and_login(client)
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    async def test_no_token(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 403
