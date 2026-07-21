from datetime import datetime
from pydantic import BaseModel, Field

class ProfileResponse(BaseModel):
    id: int
    fullName: str
    email: str
    phone: str | None = None
    role: str
    verified: bool
    createdAt: datetime

    class Config:
        from_attributes = True

class AddressRequest(BaseModel):
    label: str = Field("Home", max_length=50)
    addressLine1: str = Field(..., max_length=150)
    addressLine2: str | None = Field(None, max_length=150)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., max_length=10)

class AddressResponse(BaseModel):
    id: int
    label: str
    addressLine1: str
    addressLine2: str | None = None
    city: str
    state: str
    pincode: str

    class Config:
        from_attributes = True
