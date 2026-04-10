import pytest
import pytest_asyncio
from datetime import date, timedelta


BASE_PAYLOAD = {
    "company_name": "Acme Corp",
    "job_title": "Software Engineer",
}


@pytest_asyncio.fixture
async def application(client, auth_headers):
    response = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    return response.json()


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_application_required_fields_only(client, auth_headers):
    response = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "Acme Corp"
    assert data["job_title"] == "Software Engineer"
    assert data["status"] == "applied"
    assert data["job_url"] is None
    assert data["notes"] is None
    assert "id" in data
    assert "user_id" in data


async def test_create_application_all_fields(client, auth_headers):
    payload = {
        "company_name": "Big Tech",
        "job_title": "Senior Engineer",
        "job_url": "https://example.com/job",
        "status": "interview",
        "applied_date": str(date.today()),
        "follow_up_date": str(date.today() + timedelta(days=7)),
        "notes": "Referred by a friend",
    }
    response = await client.post("/applications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "interview"
    assert data["job_url"] == "https://example.com/job"
    assert data["notes"] == "Referred by a friend"


async def test_create_application_missing_required_field(client, auth_headers):
    response = await client.post(
        "/applications", json={"company_name": "Acme"}, headers=auth_headers
    )
    assert response.status_code == 422


async def test_create_application_invalid_status(client, auth_headers):
    response = await client.post(
        "/applications",
        json={**BASE_PAYLOAD, "status": "not_a_status"},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_create_application_unauthenticated(client):
    response = await client.post("/applications", json=BASE_PAYLOAD)
    assert response.status_code == 401


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_applications_empty(client, auth_headers):
    response = await client.get("/applications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_applications_returns_own_only(client, auth_headers, second_auth_headers):
    await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    await client.post("/applications", json=BASE_PAYLOAD, headers=second_auth_headers)

    response = await client.get("/applications", headers=auth_headers)
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


async def test_list_applications_filter_by_status(client, auth_headers):
    await client.post("/applications", json={**BASE_PAYLOAD, "status": "applied"}, headers=auth_headers)
    await client.post("/applications", json={**BASE_PAYLOAD, "status": "interview"}, headers=auth_headers)
    await client.post("/applications", json={**BASE_PAYLOAD, "status": "interview"}, headers=auth_headers)

    response = await client.get("/applications?status=interview", headers=auth_headers)
    data = response.json()
    assert data["total"] == 2
    assert all(item["status"] == "interview" for item in data["items"])


async def test_list_applications_pagination(client, auth_headers):
    for _ in range(5):
        await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)

    response = await client.get("/applications?skip=0&limit=2", headers=auth_headers)
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2


# ── Get ───────────────────────────────────────────────────────────────────────

async def test_get_application_success(client, auth_headers, application):
    response = await client.get(f"/applications/{application['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == application["id"]


async def test_get_application_not_found(client, auth_headers):
    response = await client.get("/applications/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


async def test_get_application_other_user(client, auth_headers, second_auth_headers, application):
    response = await client.get(
        f"/applications/{application['id']}", headers=second_auth_headers
    )
    assert response.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

async def test_update_application_success(client, auth_headers, application):
    response = await client.put(
        f"/applications/{application['id']}",
        json={**BASE_PAYLOAD, "status": "offer", "notes": "Great offer"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "offer"
    assert data["notes"] == "Great offer"


async def test_patch_application_partial(client, auth_headers, application):
    response = await client.patch(
        f"/applications/{application['id']}",
        json={"status": "rejected"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["company_name"] == application["company_name"]


async def test_update_application_not_found(client, auth_headers):
    response = await client.put(
        "/applications/nonexistent-id",
        json=BASE_PAYLOAD,
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_update_application_other_user(client, auth_headers, second_auth_headers, application):
    response = await client.put(
        f"/applications/{application['id']}",
        json=BASE_PAYLOAD,
        headers=second_auth_headers,
    )
    assert response.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

async def test_delete_application_success(client, auth_headers, application):
    response = await client.delete(
        f"/applications/{application['id']}", headers=auth_headers
    )
    assert response.status_code == 204

    get_response = await client.get(
        f"/applications/{application['id']}", headers=auth_headers
    )
    assert get_response.status_code == 404


async def test_delete_application_not_found(client, auth_headers):
    response = await client.delete("/applications/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


async def test_delete_application_other_user(client, auth_headers, second_auth_headers, application):
    response = await client.delete(
        f"/applications/{application['id']}", headers=second_auth_headers
    )
    assert response.status_code == 404


# ── Upcoming follow-ups ───────────────────────────────────────────────────────

async def test_upcoming_followups_within_window(client, auth_headers):
    tomorrow = str(date.today() + timedelta(days=1))
    await client.post(
        "/applications",
        json={**BASE_PAYLOAD, "follow_up_date": tomorrow},
        headers=auth_headers,
    )
    response = await client.get("/applications/upcoming?days=7", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_upcoming_followups_excludes_past(client, auth_headers):
    yesterday = str(date.today() - timedelta(days=1))
    await client.post(
        "/applications",
        json={**BASE_PAYLOAD, "follow_up_date": yesterday},
        headers=auth_headers,
    )
    response = await client.get("/applications/upcoming?days=7", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


async def test_upcoming_followups_excludes_outside_window(client, auth_headers):
    far_future = str(date.today() + timedelta(days=30))
    await client.post(
        "/applications",
        json={**BASE_PAYLOAD, "follow_up_date": far_future},
        headers=auth_headers,
    )
    response = await client.get("/applications/upcoming?days=7", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0
