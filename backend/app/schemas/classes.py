from datetime import time
from typing import Optional

from pydantic import BaseModel, Field

from app.models.gym_class import DayOfWeek


class ClassBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    trainer_name: str = Field(min_length=1, max_length=120)
    day_of_week: DayOfWeek
    start_time: time
    duration_minutes: int = Field(ge=15, le=240, default=60)
    capacity: int = Field(ge=1, le=200, default=20)


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    trainer_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=240)
    capacity: Optional[int] = Field(default=None, ge=1, le=200)


class ClassOut(ClassBase):
    id: int
    enrolled_count: int = 0

    class Config:
        from_attributes = True


class RosterMember(BaseModel):
    user_id: int
    name: str
    email: str
    enrolled_at: str
