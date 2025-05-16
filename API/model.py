from sqlalchemy import Column, Integer, String
from .database import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    insurance = Column(String)
    city = Column(String)
    phone = Column(String , nullable=True)
    services = Column(String , nullable=True)
    address = Column(String , nullable=True)
    medical_class = Column(String)



