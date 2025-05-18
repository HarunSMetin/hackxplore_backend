from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    capacity_white = Column(Float, nullable=False)  # m3
    capacity_green = Column(Float, nullable=False)  # m3
    capacity_brown = Column(Float, nullable=False)  # m3
    cost_per_km = Column(Float, default=1.8)        # € per km
    emission_per_km = Column(Float, default=1.0)    # kg CO2 per km
    average_speed = Column(Float, default=23.0)     # km/h
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Add relationship to routes
    routes = relationship("TruckRoute", back_populates="truck")