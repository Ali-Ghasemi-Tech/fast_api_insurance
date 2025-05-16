from pydantic import BaseModel
from typing import List, Optional

class HospitalOut(BaseModel):
    name: str
    insurance: str
    city: str
    medical_class: str

    class Config:
        orm_mode = True

class HospitalLocationResponse(BaseModel):
    locations: List[dict]
    failed_hospitals: List[str]
    searched_hospitals: List[str]
