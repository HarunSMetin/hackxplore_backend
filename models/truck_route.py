from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class TruckRoute(Base):
    __tablename__ = "truck_routes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    truck_id = Column(Integer, ForeignKey("trucks.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_distance_km = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    total_emissions = Column(Float, nullable=True)
    status = Column(String(50), default="planned")  # planned, in_progress, completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    truck = relationship("Truck", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan")