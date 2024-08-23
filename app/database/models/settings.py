from sqlalchemy import JSON, Boolean, Column, Integer, String

from .. import Base


class UpdateInfo(Base):
    __tablename__ = "settings.update_info"

    id = Column(Integer, unique=True, primary_key=True)
    version = Column(String, index=True)
    md5_checksum = Column(String)
    is_required = Column(Boolean)
    is_active = Column(Boolean)


class FulfilmentChinaSetting(Base):
    __tablename__ = "settings.fulfilment_china"

    tier_1_keywords = Column(JSON)
    tier_2_keywords = Column(JSON)
