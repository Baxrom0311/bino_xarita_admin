
# app/schemas/connection.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ConnectionBase(BaseModel):
    from_waypoint_id: str = Field(..., min_length=1, max_length=50)
    to_waypoint_id: str = Field(..., min_length=1, max_length=50)
    distance: float = Field(..., gt=0)

class ConnectionCreate(ConnectionBase):
    id: Optional[str] = Field(default=None, min_length=1, max_length=50)  # Endi bu majburiy emas

class Connection(ConnectionBase):
    id: Optional[str] = Field(default=None, min_length=1, max_length=50)
    
    model_config = ConfigDict(from_attributes=True)
