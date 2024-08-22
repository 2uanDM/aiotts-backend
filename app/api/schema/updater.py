from pydantic import BaseModel


class UpdateInfo(BaseModel):
    latest: str
    date: str
    detail: str


__all__ = ["UpdateInfo"]
