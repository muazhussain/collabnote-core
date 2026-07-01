from httpx import AsyncClient

_NOTE_PAYLOAD = {
    "title": "Test Note",
    "content": "This is a test note.",
}


async def _create_note(client: AsyncClient, headers: dict) -> dict:
    resp = await client.post("/api/v1/notes", json=_NOTE_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    return resp.json()


class TestCreateNote:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.post(
            "/api/v1/notes", json=_NOTE_PAYLOAD, headers=auth_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == _NOTE_PAYLOAD["title"]
        assert data["content"] == _NOTE_PAYLOAD["content"]
        assert "_id" in data

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/notes", json=_NOTE_PAYLOAD)
        assert resp.status_code == 403


class TestListNotes:
    async def test_empty(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.get("/api/v1/notes", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_user_notes(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        await _create_note(client, auth_headers)
        await _create_note(client, auth_headers)
        resp = await client.get("/api/v1/notes", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/notes")
        assert resp.status_code == 403


class TestGetNote:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        note = await _create_note(client, auth_headers)
        resp = await client.get(f"/api/v1/notes/{note['_id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["_id"] == note["_id"]

    async def test_not_found(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.get(
            "/api/v1/notes/60d5ec49f1c0d23b9a5f9e3a", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_invalid_id(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.get("/api/v1/notes/notanid", headers=auth_headers)
        assert resp.status_code == 404

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/notes/60d5ec49f1c0d23b9a5f9e3a")
        assert resp.status_code == 403


class TestUpdateNote:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        note = await _create_note(client, auth_headers)
        resp = await client.put(
            f"/api/v1/notes/{note['_id']}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert resp.json()["content"] == _NOTE_PAYLOAD["content"]

    async def test_no_fields(self, client: AsyncClient, auth_headers: dict) -> None:
        note = await _create_note(client, auth_headers)
        resp = await client.put(
            f"/api/v1/notes/{note['_id']}",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_not_found(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.put(
            "/api/v1/notes/60d5ec49f1c0d23b9a5f9e3a",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_invalid_id(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.put(
            "/api/v1/notes/notanid",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/api/v1/notes/60d5ec49f1c0d23b9a5f9e3a",
            json={"title": "Updated"},
        )
        assert resp.status_code == 403


class TestDeleteNote:
    async def test_success(self, client: AsyncClient, auth_headers: dict) -> None:
        note = await _create_note(client, auth_headers)
        resp = await client.delete(f"/api/v1/notes/{note['_id']}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_deleted_note_not_found(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        note = await _create_note(client, auth_headers)
        await client.delete(f"/api/v1/notes/{note['_id']}", headers=auth_headers)
        resp = await client.get(f"/api/v1/notes/{note['_id']}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_not_found(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.delete(
            "/api/v1/notes/60d5ec49f1c0d23b9a5f9e3a", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_invalid_id(self, client: AsyncClient, auth_headers: dict) -> None:
        resp = await client.delete("/api/v1/notes/notanid", headers=auth_headers)
        assert resp.status_code == 404

    async def test_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.delete("/api/v1/notes/60d5ec49f1c0d23b9a5f9e3a")
        assert resp.status_code == 403
