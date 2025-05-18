from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from database import get_db
from services.route_planning_service import route_planning_service
from schemas.route import (
    RouteCreateRequest,
    RouteResponse,
    RouteDetailResponse,
    RouteStatusUpdate
)
import crud.truck_route as route_crud

router = APIRouter(prefix="/route-planning", tags=["Route Planning"])

@router.post("/plan", response_model=RouteResponse)
def create_route_plan(
    request: RouteCreateRequest,
    db: Session = Depends(get_db)
):
    """Create an optimized route plan for a truck to visit containers"""
    try:
        route = route_planning_service.create_optimized_route(
            db=db,
            truck_id=request.truck_id,
            container_ids=request.container_ids,
            optimization_method=request.optimization_method
        )
        return route
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create route: {str(e)}")

@router.get("/routes/{route_id}", response_model=RouteDetailResponse)
def get_route_details(route_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a route"""
    route_details = route_planning_service.get_route_details(db, route_id)
    if not route_details:
        raise HTTPException(status_code=404, detail="Route not found")
    return route_details

@router.get("/routes/truck/{truck_id}", response_model=List[RouteResponse])
def get_truck_routes(
    truck_id: int, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all routes for a specific truck, optionally filtered by status"""
    routes = route_crud.get_routes_by_truck(db, truck_id)
    if status:
        routes = [r for r in routes if r.status == status]
    return routes

@router.put("/routes/{route_id}/status", response_model=RouteResponse)
def update_route_status(
    route_id: int,
    status_update: RouteStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update the status of a route"""
    route = route_crud.update_route_status(db, route_id, status_update.status)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Handle status-specific updates
    if status_update.status == "in_progress" and not route.actual_start:
        route.actual_start = datetime.now()
        db.commit()
    elif status_update.status == "completed" and not route.actual_end:
        route.actual_end = datetime.now()
        db.commit()
    
    return route

@router.get("/active-routes", response_model=List[RouteResponse])
def get_active_routes(db: Session = Depends(get_db)):
    """Get all active routes (in_progress status)"""
    return route_crud.get_active_routes(db)