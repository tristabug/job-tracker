from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate


async def create_application(
    db: AsyncSession, user_id: str, data: ApplicationCreate
) -> Application:
    application = Application(**data.model_dump(), user_id=user_id)
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def get_applications(
    db: AsyncSession,
    user_id: str,
    status: ApplicationStatus | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Application], int]:
    query = select(Application).where(Application.user_id == user_id)
    count_query = select(func.count()).select_from(Application).where(Application.user_id == user_id)

    if status:
        query = query.where(Application.status == status)
        count_query = count_query.where(Application.status == status)

    query = query.order_by(Application.created_at.desc()).offset(skip).limit(limit)

    results = await db.execute(query)
    total = await db.execute(count_query)
    return list(results.scalars().all()), total.scalar()


async def get_application(
    db: AsyncSession, application_id: str, user_id: str
) -> Application | None:
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_application(
    db: AsyncSession, application_id: str, user_id: str, data: ApplicationUpdate
) -> Application | None:
    application = await get_application(db, application_id, user_id)
    if not application:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    await db.commit()
    await db.refresh(application)
    return application


async def delete_application(
    db: AsyncSession, application_id: str, user_id: str
) -> bool:
    application = await get_application(db, application_id, user_id)
    if not application:
        return False
    await db.delete(application)
    await db.commit()
    return True


async def get_upcoming_followups(
    db: AsyncSession, user_id: str, days: int = 7
) -> list[Application]:
    today = date.today()
    window = today + timedelta(days=days)
    result = await db.execute(
        select(Application).where(
            Application.user_id == user_id,
            Application.follow_up_date >= today,
            Application.follow_up_date <= window,
        ).order_by(Application.follow_up_date.asc())
    )
    return list(result.scalars().all())
