from httpx import AsyncClient

_OTHER_USER = {
    "email": "other@example.com",
    "username": "otheruser",
    "password": "otherpassword123",
}


class TestGetProfile:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.get("/api/v1/users/profile", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/profile")
        assert resp.status_code == 401


class TestGetUser:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        profile = (await client.get("/api/v1/users/profile", headers=auth_headers)).json()
        resp = await client.get(f"/api/v1/users/{profile['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == profile["id"]

    async def test_not_found(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.get("/api/v1/users/99999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/1")
        assert resp.status_code == 401


class TestUpdateProfile:
    async def test_update_email(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"email": "updated@example.com"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@example.com"

    async def test_update_username(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"username": "updateduser"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "updateduser"

    async def test_update_password(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"password": "newpassword123"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "newpassword123"},
        )
        assert login.status_code == 200

    async def test_no_fields(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.patch(
            "/api/v1/users/profile", json={}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    async def test_duplicate_email(self, client: AsyncClient, auth_headers: dict) -> None:
        await client.post("/api/v1/auth/register", json=_OTHER_USER)
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"email": _OTHER_USER["email"]},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_duplicate_username(self, client: AsyncClient, auth_headers: dict) -> None:
        await client.post("/api/v1/auth/register", json=_OTHER_USER)
        resp = await client.patch(
            "/api/v1/users/profile",
            json={"username": _OTHER_USER["username"]},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.patch(
            "/api/v1/users/profile", json={"email": "x@example.com"}
        )
        assert resp.status_code == 401


class TestDeleteProfile:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.delete("/api/v1/users/profile", headers=auth_headers)
        assert resp.status_code == 204

    async def test_deleted_user_cannot_login(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        await client.delete("/api/v1/users/profile", headers=auth_headers)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpassword123"},
        )
        assert resp.status_code == 401

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.delete("/api/v1/users/profile")
        assert resp.status_code == 401
