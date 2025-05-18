from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TruckBase(BaseModel):
    name: str = Field(..., example="Truck-001")
    location_lat: float = Field(..., example=52.5200)
    location_lng: float = Field(..., example=13.4050)
    white_glass_capacity: int = Field(..., example=1000)
    green_glass_capacity: int = Field(..., example=1000)
    brown_glass_capacity: int = Field(..., example=1000)

class TruckCreate(TruckBase):
    pass

class TruckUpdate(BaseModel):
    name: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    white_glass_capacity: Optional[int] = None
    green_glass_capacity: Optional[int] = None
    brown_glass_capacity: Optional[int] = None

class Truck(TruckBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Updated from orm_mode = True for Pydantic v2