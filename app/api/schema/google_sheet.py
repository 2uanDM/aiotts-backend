from pydantic import BaseModel, Field


class SKUSToInsert(BaseModel):
    sku_id: str = Field(..., title="SKU ID to insert", example="1729464933078897337")
    color: str = Field(..., title="Color of SKU", example="Black")
    product_type: str = Field(..., title="Type of product", example="T-Shirt")
    size: str = Field(..., title="Size of product", example="XL")
    seller_sku: str = Field(..., title="Seller SKU", example="SKU-123")
    product_name: str = Field(..., title="Name of product", example="T-Shirt Black XL")


__all__ = ["SKUSToInsert"]
