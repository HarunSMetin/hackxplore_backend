from sqlalchemy.orm import Session
from database import engine
from models.truck import Truck

def seed_trucks():
    initial_trucks = [
        {
            "name": "Truck-001",
            "location_lat": 49.461,
            "location_lng": 8.4723,
            "capacity_white": 1000,  # Changed from white_glass_capacity
            "capacity_green": 800,  # Changed from green_glass_capacity
            "capacity_brown": 900   # Changed from brown_glass_capacity
        },
        {
            "name": "Truck-002",
            "location_lat": 49.493,
            "location_lng": 8.4654,
            "capacity_white": 1200,  # Changed from white_glass_capacity
            "capacity_green": 1000,  # Changed from green_glass_capacity
            "capacity_brown": 1100   # Changed from brown_glass_capacity
        }
    ]

    with Session(engine) as session:
        for truck_data in initial_trucks:
            truck = Truck(**truck_data)
            session.add(truck)
        session.commit()

if __name__ == "__main__":
    seed_trucks()