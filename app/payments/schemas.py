from decimal import Decimal
from pydantic import BaseModel

class PaymentResponse(BaseModel):
    id: int
    orderId: int
    amount: Decimal
    transactionId: str | None = None
    status: str
