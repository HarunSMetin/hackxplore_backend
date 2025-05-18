from pydantic import BaseModel
from datetime import datetime

class ContainerReadingBase(BaseModel):
    container_id: int
    timestamp: datetime
    current_fill: int

class ContainerReadingResponse(ContainerReadingBase):
    reading_id: int

    class Config:
        orm_mode = True 