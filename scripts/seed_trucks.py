from sqlalchemy.orm import Session
from database import engine
from models.truck import Truck

def seed_trucks():
    initial_trucks = [
        {
            "name": "Truck-001",
            "location_lat": 49.461,
            "location_lng": 8.4723,
            "white_glass_capacity": 1000,
            "green_glass_capacity": 800,
            "brown_glass_capacity": 900
        },
        {
            "name": "Truck-002",
            "location_lat": 49.493,
            "location_lng": 8.4654,
            "white_glass_capacity": 1200,
            "green_glass_capacity": 1000,
            "brown_glass_capacity": 1100
        }
    ]

    with Session(engine) as session:
        for truck_data in initial_trucks:
            truck = Truck(**truck_data)
            session.add(truck)
        session.commit()

if __name__ == "__main__":
    seed_trucks()