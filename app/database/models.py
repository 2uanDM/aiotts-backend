from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String

from .init import Base


class LabelInfo(Base):
    __tablename__ = "label_info"

    tracking_id = Column(String, unique=True, primary_key=True, index=True)
    scanned_info = Column(JSON)


class UUID(Base):
    __tablename__ = "uuid"

    id = Column(Integer, unique=True, primary_key=True)
    value = Column(String, index=True)


class Personnel(Base):
    __tablename__ = "personnel"

    personnel_id = Column(Integer, unique=True, primary_key=True, index=True)
    department_id = Column(Integer)
    full_name = Column(String)
    email = Column(String)
    hash_password = Column(String)
    is_default_password = Column(Boolean)
    last_login_uuid = Column(String)
    last_login_time = Column(DateTime)
