import json
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

import app.database.models as models
from app.database.crud import get_user_info, get_uuid
from app.utils import get_db, validate_apikey

router = APIRouter()


load_dotenv(override=True)

## SEARCH API ##


@router.get("/search/uuid")
def check_uuid(
    value: str,
    db: Session = Depends(get_db),
    api_key: str = Query(default=""),
):
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


@router.get("/search/user")
def search_user_by_email(
    email: str, api_key: str = Query(default=""), db: Session = Depends(get_db)
):
    validate_apikey(api_key)

    personnel: models.Personnel = get_user_info(email, db)
    if personnel is None:
        return JSONResponse(
            status_code=404,
            content={"message": "email_not_found"},
        )
    else:
        # Prepare response
        response = {
            "personnel_id": personnel.personnel_id,
            "department_id": personnel.department_id,
            "full_name": personnel.full_name,
            "is_default_password": personnel.is_default_password,
            "last_login_uuid": personnel.last_login_uuid,
            "last_login_time": personnel.last_login_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return Response(
            content=json.dumps(response, ensure_ascii=False, indent=4),
            status_code=200,
            media_type="application/json",
        )


@router.get("/search/login-expired-day")
def check_login_expired_day(api_key: str = Query(default="")):
    validate_apikey(api_key)

    expired_days: str = os.getenv("LOGIN_EXPIRED_DAYS")

    if not expired_days:  # Default value is 1 day
        return Response(content="1", status_code=200, media_type="application/text")
    else:
        return Response(
            content=expired_days, status_code=200, media_type="application/text"
        )


## GET SETTINGS ##


@router.get("/settings/telegram")
def get_telegram_settings(api_key: str = Query(default="")):
    validate_apikey(api_key)

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    telebot_channel_id: str = os.getenv("TELEGRAM_CHANNEL_ID")

    return JSONResponse(
        status_code=200,
        content={"bot_token": telegram_bot_token, "channel_id": telebot_channel_id},
    )


@router.get("/update/checksum")
def get_md5_checksum_of_update_version(
    version: str, api_key: str = Query(default=""), db: Session = Depends(get_db)
):
    validate_apikey(api_key)

    pass
