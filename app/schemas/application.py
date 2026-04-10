from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    job_title: str = Field(..., min_length=1, max_length=200)
    job_url: str | None = None
    status: ApplicationStatus = ApplicationStatus.APPLIED
    applied_date: date = Field(default_factory=date.today)
    follow_up_date: date | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=1, max_length=200)
    job_title: str | None = Field(None, min_length=1, max_length=200)
    job_url: str | None = None
    status: ApplicationStatus | None = None
    applied_date: date | None = None
    follow_up_date: date | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    job_title: str
    job_url: str | None
    status: ApplicationStatus
    applied_date: date
    follow_up_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationList(BaseModel):
    items: list[ApplicationResponse]
    total: int
    skip: int
    limit: int
