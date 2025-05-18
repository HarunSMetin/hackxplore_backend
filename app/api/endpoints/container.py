from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.models.container import Container, ContainerReading
from app.models.user import User
from app.db.database import get_db
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/nearest-readings", response_model=dict, summary="Get nearest container readings")
async def get_nearest_readings(
    timestamp: datetime = Query(..., description="Reference timestamp to find nearest readings"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the nearest readings for all unique containers to the provided timestamp.
    
    - **timestamp**: The reference timestamp to find the nearest readings
    
    Returns container locations and fullness data.
    """
    try:
        # Subquery to find the closest reading for each container
        subquery = (
            db.query(
                ContainerReading.container_id,
                func.max(ContainerReading.id).label("latest_id")
            )
            .filter(ContainerReading.timestamp <= timestamp)
            .group_by(ContainerReading.container_id)
            .subquery()
        )

        # Join with container_readings to get the actual readings
        nearest_readings = (
            db.query(
                ContainerReading,
                Container.location,
                Container.latitude,
                Container.longitude
            )
            .join(subquery, and_(
                ContainerReading.container_id == subquery.c.container_id,
                ContainerReading.id == subquery.c.latest_id
            ))
            .join(Container, ContainerReading.container_id == Container.id)
            .all()
        )

        # Format the results
        result = []
        for reading, location, latitude, longitude in nearest_readings:
            result.append({
                "container_id": reading.container_id,
                "reading_id": reading.id,
                "timestamp": reading.timestamp,
                "fullness": reading.fullness,
                "location": location,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            })

        return {"readings": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nearest readings: {str(e)}")

@router.get("/timestamp-range")
async def get_timestamp_range(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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