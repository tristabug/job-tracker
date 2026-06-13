import pytest


BASE_PAYLOAD = {
    "company_name": "Acme Corp",
    "job_title": "Software Engineer",
}


async def test_demo_user_role(client, demo_auth_headers):
    response = await client.get("/auth/me", headers=demo_auth_headers)
    assert response.json()["role"] == "demo"


# ── Applications ────────────────────────────────────────────────────────────

async def test_demo_can_list_applications(client, demo_auth_headers):
    response = await client.get("/applications", headers=demo_auth_headers)
    assert response.status_code == 200


async def test_demo_cannot_create_application(client, demo_auth_headers):
    response = await client.post("/applications", json=BASE_PAYLOAD, headers=demo_auth_headers)
    assert response.status_code == 403


async def test_demo_cannot_update_application(client, auth_headers, demo_auth_headers):
    create = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    application_id = create.json()["id"]

    response = await client.put(
        f"/applications/{application_id}",
        json={"company_name": "New Name"},
        headers=demo_auth_headers,
    )
    assert response.status_code == 403


async def test_demo_cannot_patch_application(client, auth_headers, demo_auth_headers):
    create = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    application_id = create.json()["id"]

    response = await client.patch(
        f"/applications/{application_id}",
        json={"status": "interview"},
        headers=demo_auth_headers,
    )
    assert response.status_code == 403


async def test_demo_cannot_delete_application(client, auth_headers, demo_auth_headers):
    create = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    application_id = create.json()["id"]

    response = await client.delete(f"/applications/{application_id}", headers=demo_auth_headers)
    assert response.status_code == 403


# ── Contacts ─────────────────────────────────────────────────────────────────

async def test_demo_cannot_create_contact(client, auth_headers, demo_auth_headers):
    create = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    application_id = create.json()["id"]

    response = await client.post(
        f"/applications/{application_id}/contacts",
        json={"name": "Jane Recruiter"},
        headers=demo_auth_headers,
    )
    assert response.status_code == 403


async def test_demo_cannot_update_contact(client, auth_headers, demo_auth_headers):
    create = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    application_id = create.json()["id"]
    contact = await client.post(
        f"/applications/{application_id}/contacts",
        json={"name": "Jane Recruiter"},
        headers=auth_headers,
    )
    contact_id = contact.json()["id"]

    response = await client.put(
        f"/applications/{application_id}/contacts/{contact_id}",
        json={"name": "New Name"},
        headers=demo_auth_headers,
    )
    assert response.status_code == 403


async def test_demo_cannot_delete_contact(client, auth_headers, demo_auth_headers):
    create = await client.post("/applications", json=BASE_PAYLOAD, headers=auth_headers)
    application_id = create.json()["id"]
    contact = await client.post(
        f"/applications/{application_id}/contacts",
        json={"name": "Jane Recruiter"},
        headers=auth_headers,
    )
    contact_id = contact.json()["id"]

    response = await client.delete(
        f"/applications/{application_id}/contacts/{contact_id}",
        headers=demo_auth_headers,
    )
    assert response.status_code == 403
