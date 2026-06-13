"""Seed the shared read-only demo account with sample data.

Safe to run repeatedly: if the demo account already has applications,
this does nothing.

Usage:
    python -m scripts.seed_demo
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.application import Application, ApplicationStatus
from app.models.contact import Contact
from app.models.user import User, UserRole
from app.services.auth import get_password_hash


def _sample_applications() -> list[dict]:
    today = date.today()
    return [
        {
            "company_name": "Acme Corp",
            "job_title": "Software Engineer",
            "job_url": "https://acme.example.com/careers/software-engineer",
            "status": ApplicationStatus.APPLIED,
            "applied_date": today - timedelta(days=3),
            "notes": "Applied via company careers page.",
            "contacts": [],
        },
        {
            "company_name": "TechNova",
            "job_title": "Backend Developer",
            "job_url": "https://technova.example.com/jobs/backend-developer",
            "status": ApplicationStatus.PHONE_SCREEN,
            "applied_date": today - timedelta(days=10),
            "follow_up_date": today + timedelta(days=2),
            "notes": "Recruiter screen completed, waiting on next steps.",
            "contacts": [
                {
                    "name": "Priya Shah",
                    "title": "Technical Recruiter",
                    "email": "priya.shah@technova.example.com",
                },
            ],
        },
        {
            "company_name": "Globex Inc",
            "job_title": "Full Stack Engineer",
            "job_url": "https://globex.example.com/careers/full-stack-engineer",
            "status": ApplicationStatus.INTERVIEW,
            "applied_date": today - timedelta(days=18),
            "follow_up_date": today + timedelta(days=4),
            "notes": "Onsite interview loop scheduled.",
            "contacts": [
                {
                    "name": "Marcus Lee",
                    "title": "Engineering Manager",
                    "email": "marcus.lee@globex.example.com",
                    "linkedin_url": "https://www.linkedin.com/in/marcuslee-example",
                },
            ],
        },
        {
            "company_name": "Initech",
            "job_title": "Senior Software Engineer",
            "job_url": "https://initech.example.com/jobs/senior-software-engineer",
            "status": ApplicationStatus.OFFER,
            "applied_date": today - timedelta(days=30),
            "notes": "Offer received, reviewing compensation details.",
            "contacts": [
                {
                    "name": "Dana Wilkins",
                    "title": "Hiring Manager",
                    "email": "dana.wilkins@initech.example.com",
                    "phone": "555-0142",
                },
            ],
        },
        {
            "company_name": "Umbrella Corp",
            "job_title": "DevOps Engineer",
            "status": ApplicationStatus.REJECTED,
            "applied_date": today - timedelta(days=25),
            "notes": "Rejected after the final round - they went with an internal candidate.",
            "contacts": [],
        },
        {
            "company_name": "Hooli",
            "job_title": "Platform Engineer",
            "status": ApplicationStatus.WITHDRAWN,
            "applied_date": today - timedelta(days=40),
            "notes": "Withdrew after accepting another offer.",
            "contacts": [],
        },
    ]


async def seed_demo(db: AsyncSession) -> str:
    """Ensure the shared demo account and its sample data exist."""
    result = await db.execute(select(User).where(User.email == settings.demo_email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=settings.demo_email,
            hashed_password=get_password_hash(settings.demo_password),
            full_name="Demo User",
            role=UserRole.DEMO,
        )
        db.add(user)
        await db.flush()
    elif user.role != UserRole.DEMO:
        user.role = UserRole.DEMO

    count = await db.execute(
        select(func.count()).select_from(Application).where(Application.user_id == user.id)
    )
    if count.scalar() > 0:
        await db.commit()
        return f"Demo account already seeded ({user.email})"

    applications = _sample_applications()
    for app_data in applications:
        contacts_data = app_data.pop("contacts")
        application = Application(**app_data, user_id=user.id)
        db.add(application)
        await db.flush()
        for contact_data in contacts_data:
            db.add(Contact(**contact_data, application_id=application.id, user_id=user.id))

    await db.commit()
    return f"Seeded demo account ({user.email}) with {len(applications)} applications"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        message = await seed_demo(db)
    print(message)


if __name__ == "__main__":
    asyncio.run(main())
