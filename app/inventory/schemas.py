from pydantic import BaseModel

class InventoryResponse(BaseModel):
    id: int
    productId: int
    productName: str
    quantity: int
    lowStockThreshold: int

    class Config:
        from_attributes = True
