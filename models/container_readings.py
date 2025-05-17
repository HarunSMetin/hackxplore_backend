from sqlalchemy import Column, Integer, DateTime, ForeignKey
from database import Base

class ContainerReading(Base):
    __tablename__ = "container_readings"

    reading_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    container_id = Column(Integer, ForeignKey("containers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    fill_level_litres = Column(Integer, nullable=False) 