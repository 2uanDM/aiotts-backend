from pydantic import BaseModel, Field


class SKU(BaseModel):
    sku_id: str = Field(..., title="SKU ID to search", example="1729491015689212227")


__all__ = ["SKU"]
