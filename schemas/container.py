from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ContainerBase(BaseModel):
    name: str
    address: str
    location_lat: float
    location_lng: float
    type: str
    capacity: int
    current_fill: int

class ContainerCreate(ContainerBase):
    pass

class ContainerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    type: Optional[str] = None
    capacity: Optional[int] = None
    current_fill: Optional[int] = None
    last_updated: Optional[datetime] = None

class ContainerResponse(ContainerBase):
    id: int
    last_updated: datetime

    class Config:
        orm_mode = True 