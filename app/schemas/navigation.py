
# app/schemas/navigation.py
from pydantic import BaseModel, conint
from typing import List, Optional

PositiveInt = conint(gt=0)

class NavigationRequest(BaseModel):
    start_waypoint_id: Optional[str] = None
    start_room_id: Optional[PositiveInt] = None
    end_waypoint_id: Optional[str] = None
    end_room_id: Optional[PositiveInt] = None
    kiosk_id: Optional[PositiveInt] = None

class PathStep(BaseModel):
    waypoint_id: str
    floor_id: int
    x: int
    y: int
    type: str
    label: Optional[str] = None
    instruction: Optional[str] = None

class NavigationResponse(BaseModel):
    path: List[PathStep]
    total_distance: float
    floor_changes: int
    estimated_time_minutes: float
