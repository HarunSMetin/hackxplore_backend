from sqlalchemy.orm import Session
from models.truck import Truck
from schemas.truck import TruckCreate, TruckUpdate

def create_truck(db: Session, truck: TruckCreate):
    db_truck = Truck(**truck.dict())
    db.add(db_truck)
    db.commit()
    db.refresh(db_truck)
    return db_truck

def get_truck(db: Session, truck_id: int):
    return db.query(Truck).filter(Truck.id == truck_id).first()

def get_trucks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Truck).offset(skip).limit(limit).all()

def update_truck(db: Session, truck_id: int, truck: TruckUpdate):
    db_truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if db_truck:
        update_data = truck.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_truck, key, value)
        db.commit()
        db.refresh(db_truck)
    return db_truck

def delete_truck(db: Session, truck_id: int):
    db_truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if db_truck:
        db.delete(db_truck)
        db.commit()
        return True
    return False