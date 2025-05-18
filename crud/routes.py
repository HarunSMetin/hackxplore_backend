from sqlalchemy.orm import Session
from models.truck_route import TruckRoute
from models.route_stop import RouteStop
from schemas.route import TruckRouteCreate, RouteStopCreate
from typing import List
from datetime import datetime

def get_routes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TruckRoute).offset(skip).limit(limit).all()

def get_route_by_id(db: Session, route_id: int):
    return db.query(TruckRoute).filter(TruckRoute.id == route_id).first()

def get_routes_by_truck(db: Session, truck_id: int, skip: int = 0, limit: int = 100):
    return db.query(TruckRoute).filter(TruckRoute.truck_id == truck_id).offset(skip).limit(limit).all()

def get_active_routes(db: Session):
    return db.query(TruckRoute).filter(TruckRoute.status == "in_progress").all()

def create_route(db: Session, route: TruckRouteCreate, stops: List[RouteStopCreate] = None):
    db_route = TruckRoute(**route.dict())
    db.add(db_route)
    db.flush()
    
    if stops:
        for stop in stops:
            db_stop = RouteStop(**stop.dict(), route_id=db_route.id)
            db.add(db_stop)
    
    db.commit()
    db.refresh(db_route)
    return db_route

def update_route_status(db: Session, route_id: int, status: str):
    db_route = db.query(TruckRoute).filter(TruckRoute.id == route_id).first()
    if db_route:
        db_route.status = status
        db.commit()
        db.refresh(db_route)
    return db_route

def get_stops_by_route(db: Session, route_id: int):
    return db.query(RouteStop).filter(RouteStop.route_id == route_id).order_by(RouteStop.stop_number).all()