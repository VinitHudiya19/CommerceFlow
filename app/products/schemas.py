from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class CategoryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=255)
    parentId: int | None = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    parentId: int | None = None

    class Config:
        from_attributes = True

class ProductRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0)
    categoryId: int
    active: bool = True
    imageUrl: str | None = None  # Single image helper for requests

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: Decimal
    categoryId: int
    categoryName: str | None = None
    active: bool
    images: list[str] = []
    stock: int = 0
    createdAt: datetime

    class Config:
        from_attributes = True

class PaginatedProductResponse(BaseModel):
    content: list[ProductResponse]

