import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeOut(BaseModel):
    id: uuid.UUID
    name: str
    source_filename: str | None
    extracted: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: uuid.UUID
    seq: int
    title: str
    company: str
    source: str
    extracted: dict
    created_at: datetime
    fit: dict | None = None

    model_config = {"from_attributes": True}


class JobCreateText(BaseModel):
    title: str | None = None
    text: str


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    intent: str | None
    citations: list | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
