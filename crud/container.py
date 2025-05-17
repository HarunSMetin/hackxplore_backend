from sqlalchemy.orm import Session
from models.container import Container
from schemas.container import ContainerCreate, ContainerUpdate
from datetime import datetime

# List all containers
def get_containers(db: Session):
    return db.query(Container).all()

# Get a single container by ID
def get_container(db: Session, container_id: int):
    return db.query(Container).filter(Container.id == container_id).first()

# Add a new container
def create_container(db: Session, container: ContainerCreate):
    db_container = Container(**container.dict())
    db.add(db_container)
    db.commit()
    db.refresh(db_container)
    return db_container

# Update a container
def update_container(db: Session, container_id: int, container: ContainerUpdate):
    db_container = db.query(Container).filter(Container.id == container_id).first()
    if not db_container:
        return None
    for var, value in vars(container).items():
        if value is not None:
            setattr(db_container, var, value)
    db_container.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(db_container)
    return db_container

# Delete a container
def delete_container(db: Session, container_id: int):
    db_container = db.query(Container).filter(Container.id == container_id).first()
    if not db_container:
        return None
    db.delete(db_container)
    db.commit()
    return db_container 