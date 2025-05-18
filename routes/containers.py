from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database import SessionLocal
from schemas.container import ContainerCreate, ContainerUpdate, ContainerResponse
from crud.container import get_containers, get_container, create_container, update_container, delete_container
from services.co2 import estimate_co2_emission
from typing import List
from schemas.container_readings import ContainerReadingResponse
from crud.container_readings import get_readings_by_container
from models.container_readings import ContainerReading
from models.container import Container
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[ContainerResponse])
def list_containers(db: Session = Depends(get_db)):
    return get_containers(db)

@router.get("/{container_id}", response_model=ContainerResponse)
def read_container(container_id: int, db: Session = Depends(get_db)):
    db_container = get_container(db, container_id)
    if not db_container:
        raise HTTPException(status_code=404, detail="Container not found")
    return db_container

@router.post("/", response_model=ContainerResponse)
def add_container(container: ContainerCreate, db: Session = Depends(get_db)):
    return create_container(db, container)

@router.put("/{container_id}", response_model=ContainerResponse)
def edit_container(container_id: int, container: ContainerUpdate, db: Session = Depends(get_db)):
    db_container = update_container(db, container_id, container)
    if not db_container:
        raise HTTPException(status_code=404, detail="Container not found")
    return db_container

@router.delete("/{container_id}", response_model=ContainerResponse)
def remove_container(container_id: int, db: Session = Depends(get_db)):
    db_container = delete_container(db, container_id)
    if not db_container:
        raise HTTPException(status_code=404, detail="Container not found")
    return db_container

@router.get("/{container_id}/co2", response_model=float)
def get_co2_estimate(container_id: int, delayed_hours: int = 0, db: Session = Depends(get_db)):
    db_container = get_container(db, container_id)
    if not db_container:
        raise HTTPException(status_code=404, detail="Container not found")
    return estimate_co2_emission(
        db_container.current_fill,
        db_container.capacity,
        db_container.last_updated,
        db_container.location_lat,
        db_container.location_lng,
        delayed_hours=delayed_hours
    )

@router.get("/{container_id}/readings", response_model=List[ContainerReadingResponse])
def get_container_readings(container_id: int, db: Session = Depends(get_db)):
    readings = get_readings_by_container(db, container_id)
    return readings

@router.get("/readings/nearest")
def get_nearest_readings(
    timestamp: datetime,
    db: Session = Depends(get_db)
):
    """
    Get the nearest readings for all unique containers to the provided timestamp.
    Returns container locations and fullness data.
    """
    try:
        # Subquery to find the closest reading for each container
        subquery = (
            db.query(
                ContainerReading.container_id,
                func.max(ContainerReading.reading_id).label("latest_id")
            )
            .filter(ContainerReading.timestamp <= timestamp)
            .group_by(ContainerReading.container_id)
            .subquery()
        )

        # Join with container_readings to get the actual readings
        readings_query = (
            db.query(ContainerReading)
            .join(subquery, and_(
                ContainerReading.container_id == subquery.c.container_id,
                ContainerReading.reading_id == subquery.c.latest_id
            ))
        )
        
        # Get the containers info
        containers = {
            c.id: c for c in db.query(Container).filter(
                Container.id.in_([r.container_id for r in readings_query])
            )
        }
        
        # Format the results
        result = []
        for reading in readings_query:
            container = containers.get(reading.container_id)
            if container:
                result.append({
                    "container_id": reading.container_id,
                    "reading_id": reading.reading_id,
                    "timestamp": reading.timestamp,
                    "fill_level": reading.fill_level_litres,
                    "location": container.address,
                    "coordinates": {
                        "latitude": container.location_lat,
                        "longitude": container.location_lng
                    }
                })

        return {"readings": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nearest readings: {str(e)}")

@router.get("/readings/timestamp-range")
def get_timestamp_range(db: Session = Depends(get_db)):
    """
    Get the minimum (earliest) and maximum (latest) timestamps from all container readings.
    """
    try:
        # Query to find the minimum and maximum timestamps
        result = db.query(
            func.min(ContainerReading.timestamp).label("min_timestamp"),
            func.max(ContainerReading.timestamp).label("max_timestamp")
        ).first()
        
        # Handle case where there are no readings
        if result.min_timestamp is None or result.max_timestamp is None:
            return {
                "min_timestamp": None,
                "max_timestamp": None,
                "message": "No container readings found in the database"
            }
        
        return {
            "min_timestamp": result.min_timestamp,
            "max_timestamp": result.max_timestamp
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timestamp range: {str(e)}")