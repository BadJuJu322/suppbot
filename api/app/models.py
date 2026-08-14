from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


class SenderType(str, Enum):
    user = "user"
    operator = "operator"


class Operator(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    display_name: str = ""
    is_allowed: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_telegram_id: int = Field(index=True)
    user_display_name: str = ""
    status: ChatStatus = Field(default=ChatStatus.open, index=True)
    claimed_by_id: Optional[int] = Field(default=None, foreign_key="operator.id", index=True)
    claimed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id", index=True)
    sender_type: SenderType
    operator_id: Optional[int] = Field(default=None, foreign_key="operator.id")
    text: str
    created_at: datetime = Field(default_factory=utcnow, index=True)
