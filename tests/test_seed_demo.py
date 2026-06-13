from sqlalchemy import func, select
from app.config import settings
from app.models.application import Application
from app.models.contact import Contact
from app.models.user import User, UserRole
from app.services.auth import create_user
from scripts.seed_demo import seed_demo


async def test_seed_demo_creates_demo_user_and_applications(db):
    message = await seed_demo(db)

    user = (await db.execute(
        select(User).where(User.email == settings.demo_email)
    )).scalar_one()
    assert user.role == UserRole.DEMO

    app_count = (await db.execute(
        select(func.count()).select_from(Application).where(Application.user_id == user.id)
    )).scalar()
    assert app_count > 0
    assert "Seeded" in message


async def test_seed_demo_seeds_contacts(db):
    await seed_demo(db)

    user = (await db.execute(
        select(User).where(User.email == settings.demo_email)
    )).scalar_one()

    contact_count = (await db.execute(
        select(func.count()).select_from(Contact).where(Contact.user_id == user.id)
    )).scalar()
    assert contact_count > 0


async def test_seed_demo_is_idempotent(db):
    await seed_demo(db)

    user = (await db.execute(
        select(User).where(User.email == settings.demo_email)
    )).scalar_one()
    app_count_first = (await db.execute(
        select(func.count()).select_from(Application).where(Application.user_id == user.id)
    )).scalar()

    second_message = await seed_demo(db)

    app_count_second = (await db.execute(
        select(func.count()).select_from(Application).where(Application.user_id == user.id)
    )).scalar()

    assert app_count_first == app_count_second
    assert "already seeded" in second_message


async def test_seed_demo_fixes_existing_user_role(db):
    existing = await create_user(db, settings.demo_email, "SomeOtherPassword1!", "Existing User")
    assert existing.role == UserRole.USER

    await seed_demo(db)

    user = (await db.execute(
        select(User).where(User.email == settings.demo_email)
    )).scalar_one()
    assert user.role == UserRole.DEMO


async def test_seed_demo_account_is_read_only(client, db):
    await seed_demo(db)

    login = await client.post("/auth/login", data={
        "username": settings.demo_email,
        "password": settings.demo_password,
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    list_response = await client.get("/applications", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] > 0

    create_response = await client.post(
        "/applications",
        json={"company_name": "New Co", "job_title": "Engineer"},
        headers=headers,
    )
    assert create_response.status_code == 403
