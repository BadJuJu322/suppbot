import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import update
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.deps import get_current_operator
from app.models import Chat, ChatStatus, Message, Operator, SenderType, utcnow
from app.schemas import ChatOut, IncomingMessageIn, MessageOut, SendMessageIn
from app.security import validate_init_data
from app.ws import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/internal/incoming-message")
async def incoming_message(
    payload: IncomingMessageIn,
    x_internal_secret: str = Header(default=""),
    session: Session = Depends(get_session),
):
    if x_internal_secret != settings.bot_internal_secret:
        raise HTTPException(401, "bad internal secret")

    chat = session.exec(
        select(Chat).where(
            Chat.user_telegram_id == payload.telegram_user_id,
            Chat.status != ChatStatus.closed,
        )
    ).first()
    if chat is None:
        chat = Chat(
            user_telegram_id=payload.telegram_user_id,
            user_display_name=payload.username or payload.first_name,
        )
        session.add(chat)
        session.commit()
        session.refresh(chat)

    message = Message(chat_id=chat.id, sender_type=SenderType.user, text=payload.text)
    chat.updated_at = message.created_at
    session.add(message)
    session.add(chat)
    session.commit()

    await manager.broadcast({"type": "chat_updated", "chat_id": chat.id})
    return {"ok": True, "chat_id": chat.id}


# ---------------------------------------------------------------------------
# operator-facing
# ---------------------------------------------------------------------------

@router.get("/me")
async def get_me(operator: Operator = Depends(get_current_operator)):
    return {"id": operator.id, "telegram_id": operator.telegram_id, "display_name": operator.display_name}


@router.get("/chats", response_model=list[ChatOut])
async def list_chats(
    status: Optional[ChatStatus] = None,
    session: Session = Depends(get_session),
    operator: Operator = Depends(get_current_operator),
):
    query = select(Chat)
    if status:
        query = query.where(Chat.status == status)
    chats = session.exec(query.order_by(Chat.updated_at.desc())).all()

    names = {op.id: op.display_name for op in session.exec(select(Operator)).all()}

    last_messages: dict[int, Message] = {}
    chat_ids = [c.id for c in chats]
    if chat_ids:
        for m in session.exec(
            select(Message).where(Message.chat_id.in_(chat_ids)).order_by(Message.created_at)
        ).all():
            last_messages[m.chat_id] = m

    return [
        ChatOut(
            **chat.model_dump(),
            claimed_by_name=names.get(chat.claimed_by_id),
            last_message=last_messages[chat.id].text if chat.id in last_messages else None,
            last_message_at=last_messages[chat.id].created_at if chat.id in last_messages else None,
        )
        for chat in chats
    ]


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def get_messages(
    chat_id: int,
    session: Session = Depends(get_session),
    operator: Operator = Depends(get_current_operator),
):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(404, "chat not found")
    return session.exec(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    ).all()


@router.post("/chats/{chat_id}/claim", response_model=ChatOut)
async def claim_chat(
    chat_id: int,
    session: Session = Depends(get_session),
    operator: Operator = Depends(get_current_operator),
):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(404, "chat not found")
    if chat.status == ChatStatus.closed:
        raise HTTPException(409, "chat is closed")

    if chat.claimed_by_id == operator.id:
        return ChatOut(**chat.model_dump(), claimed_by_name=operator.display_name)

    stmt = (
        update(Chat)
        .where(Chat.id == chat_id, Chat.claimed_by_id.is_(None))
        .values(claimed_by_id=operator.id, status=ChatStatus.in_progress, claimed_at=utcnow(), updated_at=utcnow())
    )
    result = session.execute(stmt)
    session.commit()

    if result.rowcount == 0:
        raise HTTPException(409, "chat already claimed by another operator")

    session.refresh(chat)
    await manager.broadcast({"type": "chat_updated", "chat_id": chat.id})
    return ChatOut(**chat.model_dump(), claimed_by_name=operator.display_name)


@router.post("/chats/{chat_id}/release", response_model=ChatOut)
async def release_chat(
    chat_id: int,
    session: Session = Depends(get_session),
    operator: Operator = Depends(get_current_operator),
):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(404, "chat not found")

    stmt = (
        update(Chat)
        .where(Chat.id == chat_id, Chat.claimed_by_id == operator.id)
        .values(claimed_by_id=None, claimed_at=None, status=ChatStatus.open, updated_at=utcnow())
    )
    result = session.execute(stmt)
    session.commit()
    if result.rowcount == 0:
        raise HTTPException(409, "chat is not claimed by you")

    session.refresh(chat)
    await manager.broadcast({"type": "chat_updated", "chat_id": chat.id})
    return ChatOut(**chat.model_dump(), claimed_by_name=None)


@router.post("/chats/{chat_id}/close", response_model=ChatOut)
async def close_chat(
    chat_id: int,
    session: Session = Depends(get_session),
    operator: Operator = Depends(get_current_operator),
):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(404, "chat not found")

    stmt = (
        update(Chat)
        .where(Chat.id == chat_id, Chat.claimed_by_id == operator.id)
        .values(status=ChatStatus.closed, updated_at=utcnow())
    )
    result = session.execute(stmt)
    session.commit()
    if result.rowcount == 0:
        raise HTTPException(409, "chat is not claimed by you")

    session.refresh(chat)
    await manager.broadcast({"type": "chat_updated", "chat_id": chat.id})
    return ChatOut(**chat.model_dump(), claimed_by_name=operator.display_name)


@router.post("/chats/{chat_id}/messages", response_model=MessageOut)
async def send_message(
    chat_id: int,
    payload: SendMessageIn,
    session: Session = Depends(get_session),
    operator: Operator = Depends(get_current_operator),
):
    chat = session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(404, "chat not found")
    if chat.claimed_by_id != operator.id:
        raise HTTPException(409, "claim the chat before replying")
    if chat.status == ChatStatus.closed:
        raise HTTPException(409, "chat is closed")

    message = Message(chat_id=chat_id, sender_type=SenderType.operator, operator_id=operator.id, text=payload.text)
    chat.updated_at = message.created_at
    session.add(message)
    session.add(chat)
    session.commit()
    session.refresh(message)

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                f"{settings.bot_internal_url}/internal/send",
                json={"telegram_user_id": chat.user_telegram_id, "text": payload.text},
                headers={"X-Internal-Secret": settings.bot_internal_secret},
            )
            resp.raise_for_status()
    except Exception:
        logger.exception("не удалось доставить сообщение пользователю через bot")

    await manager.broadcast({"type": "chat_updated", "chat_id": chat.id})
    return message



@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):

    init_data = websocket.query_params.get("init_data", "")
    telegram_id: Optional[int] = None

    if settings.dev_mode and init_data.startswith("dev:"):
        telegram_id = int(init_data.split(":", 1)[1])
    else:
        parsed = validate_init_data(init_data, settings.bot_token)
        if parsed and "user" in parsed:
            telegram_id = parsed["user"]["id"]

    if telegram_id not in settings.allowed_operator_ids:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
