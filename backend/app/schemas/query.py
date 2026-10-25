from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import QueryStatus


class QueryCreate(BaseModel):
    message: str = Field(min_length=3, max_length=10000)
    due_at: datetime | None = None


class QueryOut(BaseModel):
    id: int
    application_id: int
    raised_by_id: int | None
    message: str
    due_at: datetime | None
    status: QueryStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class QueryResponseCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10000)


class QueryResponseOut(BaseModel):
    id: int
    query_id: int
    responder_id: int | None
    message: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
