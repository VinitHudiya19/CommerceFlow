from datetime import datetime
from pydantic import BaseModel, Field

class ReviewRequest(BaseModel):
    productId: int
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=2, max_length=1000)

class ReviewResponse(BaseModel):
    id: int
    productId: int
    userId: int
    userName: str
    rating: int
    comment: str
    createdAt: datetime

    class Config:
        from_attributes = True

class AISummaryResponse(BaseModel):
    summary: str
