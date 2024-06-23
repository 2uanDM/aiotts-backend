from sqlalchemy.orm import Session

from . import models


def get_label_info(tracking_id: str, db: Session) -> models.LabelInfo:
    return (
        db.query(models.LabelInfo)
        .filter(models.LabelInfo.tracking_id == tracking_id)
        .first()
    )


def get_uuid(uuid: str, db: Session) -> models.UUID:
    return db.query(models.UUID).filter(models.UUID.value == uuid).first()


def get_password_status(email: str, db: Session) -> models.Personnel:
    return db.query(models.Personnel).filter(models.Personnel.email == email).first()
