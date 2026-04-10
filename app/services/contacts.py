from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


async def create_contact(
    db: AsyncSession, application_id: str, user_id: str, data: ContactCreate
) -> Contact:
    contact = Contact(**data.model_dump(), application_id=application_id, user_id=user_id)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_contacts(
    db: AsyncSession, application_id: str, user_id: str
) -> list[Contact]:
    result = await db.execute(
        select(Contact).where(
            Contact.application_id == application_id,
            Contact.user_id == user_id,
        ).order_by(Contact.created_at.asc())
    )
    return list(result.scalars().all())


async def get_contact(
    db: AsyncSession, contact_id: str, application_id: str, user_id: str
) -> Contact | None:
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.application_id == application_id,
            Contact.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_contact(
    db: AsyncSession, contact_id: str, application_id: str, user_id: str, data: ContactUpdate
) -> Contact | None:
    contact = await get_contact(db, contact_id, application_id, user_id)
    if not contact:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(
    db: AsyncSession, contact_id: str, application_id: str, user_id: str
) -> bool:
    contact = await get_contact(db, contact_id, application_id, user_id)
    if not contact:
        return False
    await db.delete(contact)
    await db.commit()
    return True
