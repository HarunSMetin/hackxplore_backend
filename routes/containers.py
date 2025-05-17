from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas.container import ContainerCreate, ContainerUpdate, ContainerResponse
from crud.container import get_containers, get_container, create_container, update_container, delete_container
from services.co2 import estimate_co2_emission
from typing import List
from schemas.container_readings import ContainerReadingResponse
from crud.container_readings import get_readings_by_container

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