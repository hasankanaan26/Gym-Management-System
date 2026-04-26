from datetime import datetime

from pydantic import BaseModel

from app.schemas.classes import ClassOut


class EnrollmentCreate(BaseModel):
    class_id: int


class EnrollmentOut(BaseModel):
    id: int
    class_id: int
    user_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True


class MyEnrollmentOut(BaseModel):
    id: int
    enrolled_at: datetime
    gym_class: ClassOut

    class Config:
        from_attributes = True
