from sqlalchemy import JSON, Column, String

from .. import Base


class LabelInfo(Base):
    __tablename__ = "label_info"

    tracking_id = Column(String, unique=True, primary_key=True, index=True)
    scanned_info = Column(JSON)
