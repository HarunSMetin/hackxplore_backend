from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class Container(Base):
    __tablename__ = "containers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False, default="")
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    current_fill = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow) 