from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
