from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.models import Operator
from app.security import validate_init_data


def get_current_operator(
    authorization: str = Header(default=""),
    session: Session = Depends(get_session),
) -> Operator:
    telegram_id: int | None = None
    display_name = ""

    if settings.dev_mode and authorization.startswith("dev "):
        telegram_id = int(authorization[4:])
        display_name = f"dev-{telegram_id}"
    elif authorization.startswith("tma "):
        parsed = validate_init_data(authorization[4:], settings.bot_token)
        if parsed is None or "user" not in parsed:
            raise HTTPException(401, "invalid telegram auth")
        telegram_id = parsed["user"]["id"]
        display_name = parsed["user"].get("username") or parsed["user"].get("first_name", "")
    else:
        raise HTTPException(401, "missing telegram auth")

    if telegram_id not in settings.allowed_operator_ids:
        raise HTTPException(403, "operator not in allowlist")

    operator = session.exec(select(Operator).where(Operator.telegram_id == telegram_id)).first()
    if operator is None:
        operator = Operator(telegram_id=telegram_id, display_name=display_name, is_allowed=True)
        session.add(operator)
        session.commit()
        session.refresh(operator)
    elif operator.display_name != display_name:
        operator.display_name = display_name
        session.add(operator)
        session.commit()
        session.refresh(operator)
    return operator
