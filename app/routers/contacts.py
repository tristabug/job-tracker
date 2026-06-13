from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_write_access
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.services import contacts as contact_service
from app.services import applications as application_service

router = APIRouter(prefix="/applications/{application_id}/contacts", tags=["contacts"])


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    application_id: str,
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    application = await application_service.get_application(db, application_id, current_user.id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return await contact_service.create_contact(db, application_id, current_user.id, data)


@router.get("", response_model=list[ContactResponse])
async def list_contacts(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = await application_service.get_application(db, application_id, current_user.id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return await contact_service.get_contacts(db, application_id, current_user.id)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    application_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = await contact_service.get_contact(db, contact_id, application_id, current_user.id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    application_id: str,
    contact_id: str,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    contact = await contact_service.update_contact(
        db, contact_id, application_id, current_user.id, data
    )
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    application_id: str,
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_write_access),
):
    deleted = await contact_service.delete_contact(
        db, contact_id, application_id, current_user.id
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
