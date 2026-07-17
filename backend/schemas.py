from datetime import datetime

from pydantic import BaseModel, Field


class LeadSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\+380\d{9}$")
    service: str = Field(..., min_length=2, max_length=120)
    comment: str | None = None


class StatusUpdateSchema(BaseModel):
    status: str = Field(..., pattern=r"^(Новий|В процесі|Оброблено|Відкладено)$")


class AdminLoginSchema(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)


class LeadResponseSchema(LeadSchema):
    id: int
    status: str
    created_at: datetime
