from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class OrderRequest(BaseModel):
    addressId: int

class OrderItemResponse(BaseModel):
    id: int
    productId: int | None = None
    productName: str
    quantity: int
    unitPrice: Decimal
    subtotal: Decimal

class OrderResponse(BaseModel):
    id: int
    userId: int
    totalAmount: Decimal
    status: str
    deliveryAddress: str
    createdAt: datetime
    items: list[OrderItemResponse] = []
