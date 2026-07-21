from decimal import Decimal
from pydantic import BaseModel, Field

class CartItemRequest(BaseModel):
    productId: int
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    id: int
    productId: int
    productName: str
    unitPrice: Decimal
    quantity: int
    subtotal: Decimal
    productImageUrl: str | None = None

class CartResponse(BaseModel):
    id: int
    userId: int
    items: list[CartItemResponse] = []
    totalAmount: Decimal
