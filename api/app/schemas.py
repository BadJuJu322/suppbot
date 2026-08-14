from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models import ChatStatus, SenderType


class ChatOut(BaseModel):
    id: int
    user_telegram_id: int
    user_display_name: str
    status: ChatStatus
    claimed_by_id: Optional[int]
    claimed_by_name: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_type: SenderType
    operator_id: Optional[int]
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageIn(BaseModel):
    text: str


class IncomingMessageIn(BaseModel):
    telegram_user_id: int
    username: str = ""
    first_name: str = ""
    text: str
