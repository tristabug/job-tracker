import pytest_asyncio


BASE_APP_PAYLOAD = {
    "company_name": "Acme Corp",
    "job_title": "Software Engineer",
}

BASE_CONTACT_PAYLOAD = {
    "name": "Jane Smith",
    "title": "Engineering Manager",
    "email": "jane@acme.com",
}


@pytest_asyncio.fixture
async def application(client, auth_headers):
    response = await client.post("/applications", json=BASE_APP_PAYLOAD, headers=auth_headers)
    app_data = response.json()
    yield app_data
    try:
        await client.delete(f"/applications/{app_data['id']}", headers=auth_headers)
    except Exception:
        pass


@pytest_asyncio.fixture
async def contact(client, auth_headers, application):
    response = await client.post(
        f"/applications/{application['id']}/contacts",
        json=BASE_CONTACT_PAYLOAD,
        headers=auth_headers,
    )
    contact_data = response.json()
    yield contact_data
    try:
        await client.delete(
            f"/applications/{application['id']}/contacts/{contact_data['id']}",
            headers=auth_headers,
        )
    except Exception:
        pass


# ── Create ────────────────────────────────────────────────────────────────────

async def test_create_contact_success(client, auth_headers, application):
    response = await client.post(
        f"/applications/{application['id']}/contacts",
        json=BASE_CONTACT_PAYLOAD,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["email"] == "jane@acme.com"
    assert data["application_id"] == application["id"]
    assert "id" in data


async def test_create_contact_required_field_only(client, auth_headers, application):
    response = await client.post(
        f"/applications/{application['id']}/contacts",
        json={"name": "John Doe"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] is None
    assert data["title"] is None


async def test_create_contact_application_not_found(client, auth_headers):
    response = await client.post(
        "/applications/nonexistent-id/contacts",
        json=BASE_CONTACT_PAYLOAD,
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_create_contact_other_user_application(
    client, auth_headers, second_auth_headers, application
):
    response = await client.post(
        f"/applications/{application['id']}/contacts",
        json=BASE_CONTACT_PAYLOAD,
        headers=second_auth_headers,
    )
    assert response.status_code == 404


async def test_create_contact_missing_name(client, auth_headers, application):
    response = await client.post(
        f"/applications/{application['id']}/contacts",
        json={"email": "no-name@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ── List ──────────────────────────────────────────────────────────────────────

async def test_list_contacts(client, auth_headers, application):
    await client.post(
        f"/applications/{application['id']}/contacts",
        json={"name": "Contact One"},
        headers=auth_headers,
    )
    await client.post(
        f"/applications/{application['id']}/contacts",
        json={"name": "Contact Two"},
        headers=auth_headers,
    )
    response = await client.get(
        f"/applications/{application['id']}/contacts", headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_contacts_application_not_found(client, auth_headers):
    response = await client.get(
        "/applications/nonexistent-id/contacts", headers=auth_headers
    )
    assert response.status_code == 404


# ── Get ───────────────────────────────────────────────────────────────────────

async def test_get_contact_success(client, auth_headers, application, contact):
    response = await client.get(
        f"/applications/{application['id']}/contacts/{contact['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == contact["id"]


async def test_get_contact_not_found(client, auth_headers, application):
    response = await client.get(
        f"/applications/{application['id']}/contacts/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

async def test_update_contact_success(client, auth_headers, application, contact):
    response = await client.put(
        f"/applications/{application['id']}/contacts/{contact['id']}",
        json={**BASE_CONTACT_PAYLOAD, "title": "VP of Engineering"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "VP of Engineering"


async def test_update_contact_not_found(client, auth_headers, application):
    response = await client.put(
        f"/applications/{application['id']}/contacts/nonexistent-id",
        json=BASE_CONTACT_PAYLOAD,
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

async def test_delete_contact_success(client, auth_headers, application, contact):
    response = await client.delete(
        f"/applications/{application['id']}/contacts/{contact['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    get_response = await client.get(
        f"/applications/{application['id']}/contacts/{contact['id']}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


async def test_delete_contact_not_found(client, auth_headers, application):
    response = await client.delete(
        f"/applications/{application['id']}/contacts/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Cascade ───────────────────────────────────────────────────────────────────

async def test_delete_application_cascades_to_contacts(client, auth_headers, application, contact):
    await client.delete(f"/applications/{application['id']}", headers=auth_headers)

    response = await client.post(
        "/applications", json=BASE_APP_PAYLOAD, headers=auth_headers
    )
    new_app = response.json()

    contacts_response = await client.get(
        f"/applications/{new_app['id']}/contacts", headers=auth_headers
    )
    assert contacts_response.json() == []
