from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
import uuid


PROPERTY_TYPES = ["apartment", "house", "villa", "plot", "commercial"]


class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    city: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=500)
    price: Decimal = Field(..., gt=0)
    bedrooms: int = Field(default=1, ge=0, le=50)
    bathrooms: int = Field(default=1, ge=0, le=20)
    property_type: str = Field(default="apartment")


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0, le=50)
    bathrooms: Optional[int] = Field(None, ge=0, le=20)
    property_type: Optional[str] = None


class PropertyResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    city: str
    address: str
    price: Decimal
    bedrooms: int
    bathrooms: int
    property_type: str
    owner_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PropertyFilter(BaseModel):
    city: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
