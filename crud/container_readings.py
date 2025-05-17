from sqlalchemy.orm import Session
from models.container_readings import ContainerReading
from typing import List

def get_readings_by_container(db: Session, container_id: int) -> List[ContainerReading]:
    return db.query(ContainerReading).filter(ContainerReading.container_id == container_id).order_by(ContainerReading.timestamp.desc()).all() 