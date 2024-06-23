from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.database.crud import get_label_info
from app.database.init import SessionLocal
from app.database.models import LabelInfo

router = APIRouter()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search/{tracking_id}")
def search_label(tracking_id: str, db: Session = Depends(get_db)):
    label: LabelInfo = get_label_info(tracking_id, db)
    if label is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": f"Label with tracking_id {tracking_id} not found",
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": label.scanned_info.get("data"),
        },
    )
