from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("truck_routes.id", ondelete="CASCADE"))
    container_id = Column(Integer, ForeignKey("containers.id"))
    stop_number = Column(Integer, nullable=False)
    planned_arrival_time = Column(DateTime, nullable=False)
    actual_arrival_time = Column(DateTime, nullable=True)
    collected_white_glass_m3 = Column(Float, default=0.0)
    collected_green_glass_m3 = Column(Float, default=0.0)
    collected_brown_glass_m3 = Column(Float, default=0.0)
    
    # Relationships
    route = relationship("TruckRoute", back_populates="stops")
    container = relationship("Container")