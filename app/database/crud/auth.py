from sqlalchemy.orm import Session

from .. import models


def get_uuid(uuid: str, db: Session) -> models.UUID | None:
    return db.query(models.UUID).filter(models.UUID.value == uuid).first()


def get_user_info(email: str, db: Session) -> models.Personnel | None:
    return db.query(models.Personnel).filter(models.Personnel.email == email).first()
