from decimal import Decimal
from pydantic import BaseModel

class WishlistResponse(BaseModel):
    id: int
    productId: int
    productName: str
    productPrice: Decimal | None = None
    productImageUrl: str | None = None

    class Config:
        from_attributes = True
