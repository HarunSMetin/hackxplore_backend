from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.truck import Truck, TruckCreate, TruckUpdate
from crud import truck as truck_crud

router = APIRouter()

@router.post("/", response_model=Truck)
def create_truck(truck: TruckCreate, db: Session = Depends(get_db)):
    return truck_crud.create_truck(db=db, truck=truck)

@router.get("/", response_model=List[Truck])
def read_trucks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trucks = truck_crud.get_trucks(db, skip=skip, limit=limit)
    return trucks

@router.get("/{truck_id}", response_model=Truck)
def read_truck(truck_id: int, db: Session = Depends(get_db)):
    db_truck = truck_crud.get_truck(db, truck_id=truck_id)
    if db_truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")
    return db_truck

@router.put("/{truck_id}", response_model=Truck)
def update_truck(truck_id: int, truck: TruckUpdate, db: Session = Depends(get_db)):
    db_truck = truck_crud.update_truck(db, truck_id=truck_id, truck=truck)
    if db_truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")
    return db_truck

@router.delete("/{truck_id}")
def delete_truck(truck_id: int, db: Session = Depends(get_db)):
    success = truck_crud.delete_truck(db, truck_id=truck_id)
    if not success:
        raise HTTPException(status_code=404, detail="Truck not found")
    return {"message": "Truck deleted successfully"}