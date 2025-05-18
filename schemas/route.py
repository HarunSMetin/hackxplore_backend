from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Create schemas
class RouteStopCreate(BaseModel):
    container_id: int
    stop_number: int
    status: str = "pending"
    estimated_fill_level: Optional[float] = None

class TruckRouteCreate(BaseModel):
    truck_id: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    status: str = "planned"
    estimated_distance: Optional[float] = None
    estimated_duration: Optional[float] = None
    estimated_emissions: Optional[float] = None
    estimated_cost: Optional[float] = None
    scheduled_start: Optional[datetime] = None

# Request schemas
class RouteCreateRequest(BaseModel):
    truck_id: int
    container_ids: List[int]
    optimization_method: str = Field(
        default="distance", 
        description="Optimization method: 'distance', 'capacity_optimized', etc."
    )
    scheduled_start: Optional[datetime] = None

class RouteStatusUpdate(BaseModel):
    status: str = Field(..., description="Route status: 'planned', 'in_progress', 'completed', 'cancelled'")
    actual_distance: Optional[float] = None
    actual_duration: Optional[float] = None

# Response schemas
class RouteStopResponse(BaseModel):
    id: int
    container_id: int
    stop_number: int
    status: str
    estimated_fill_level: Optional[float] = None
    actual_fill_level: Optional[float] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class RouteResponse(BaseModel):
    id: int
    truck_id: int
    status: str
    estimated_distance: Optional[float] = None
    estimated_duration: Optional[float] = None
    estimated_emissions: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_distance: Optional[float] = None
    actual_duration: Optional[float] = None
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class RouteDetailResponse(BaseModel):
    route_id: int
    status: str
    truck: Dict[str, Any]
    metrics: Dict[str, Any]
    schedule: Dict[str, Any]
    stops: List[Dict[str, Any]]
    
    class Config:
        orm_mode = True