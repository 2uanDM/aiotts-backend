from sqlalchemy.orm import Session

from .. import models


def get_label_info(tracking_id: str, db: Session) -> models.LabelInfo | None:
    return (
        db.query(models.LabelInfo)
        .filter(models.LabelInfo.tracking_id == tracking_id)
        .first()
    )
