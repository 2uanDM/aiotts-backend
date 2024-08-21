import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

import app.database.models as models
from app.database.crud import get_password_status, get_uuid
from app.utils import get_db, validate_apikey

router = APIRouter()


load_dotenv(override=True)


@router.get("/search/uuid", tags=["Authentication"])
def check_uuid(
    value: str,
    db: Session = Depends(get_db),
    api_key: str = Query(default=""),
):
    # Raise 401 if the API key is invalid
    validate_apikey(api_key)

    uuid: models.UUID = get_uuid(value, db)
    if uuid is None:
        return JSONResponse(
            status_code=404,
            content={"status": "not_found"},
        )

    return JSONResponse(
        status_code=200,
        content={"status": "found"},
    )


@router.get("/search/password-status", tags=["Authentication"])
def check_password_status(
    email: str, api_key: str = Query(default=""), db: Session = Depends(get_db)
):
    # Raise 401 if the API key is invalid
    validate_apikey(api_key)

    personnel: models.Personnel = get_password_status(email, db)
    if personnel is None:
        return JSONResponse(
            status_code=404,
            content={"message": "email_not_found"},
        )
    else:
        if personnel.is_default_password:
            return JSONResponse(
                status_code=200,
                content={"status": "default"},
            )

        return JSONResponse(
            status_code=200,
            content={"status": "changed"},
        )


@router.get("/search/login-expired-day", tags=["Authentication"])
def check_login_expired_day(api_key: str = Query(default="")):
    # Raise 401 if the API key is invalid
    validate_apikey(api_key)

    expired_days: str = os.getenv("LOGIN_EXPIRED_DAYS")

    if not expired_days:  # Default value is 1 day
        return Response(content="1", status_code=200, media_type="application/text")
    else:
        return Response(
            content=expired_days, status_code=200, media_type="application/text"
        )


@router.get("/settings/telegram", tags=["Authentication"])
def get_telegram_settings(api_key: str = Query(default="")):
    # Raise 401 if the API key is invalid
    validate_apikey(api_key)

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    telebot_channel_id: str = os.getenv("TELEGRAM_CHANNEL_ID")

    return JSONResponse(
        status_code=200,
        content={"bot_token": telegram_bot_token, "channel_id": telebot_channel_id},
    )
