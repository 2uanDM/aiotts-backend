import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

import app.database.models as models
from app.database.crud import get_password_status, get_uuid
from app.database.init import SessionLocal

router = APIRouter()


load_dotenv(override=True)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search/uuid", tags=["Authentication"])
def check_uuid(value: str, db: Session = Depends(get_db)):
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
def check_password_status(email: str, db: Session = Depends(get_db)):
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
def check_login_expired_day():
    expired_days: str = os.getenv("LOGIN_EXPIRED_DAYS")

    if not expired_days:  # Default value is 1 day
        return Response(content="1", status_code=200, media_type="application/text")
    else:
        return Response(
            content=expired_days, status_code=200, media_type="application/text"
        )
