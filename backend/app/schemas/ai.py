from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    application_id: int | None = None
    conversation_id: int | None = None


class ChatSource(BaseModel):
    type: str
    id: str
    label: str


class SuggestedAction(BaseModel):
    label: str
    route: str


class ChatMessageOut(BaseModel):
    conversation_id: int
    answer: str
    sources: list[ChatSource]
    suggested_actions: list[SuggestedAction]
    used_ai: bool
    needs_human_review: bool


class StoredChatMessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SummaryOut(BaseModel):
    application_id: int
    summary: str
    next_action: str
    generated_by: str
