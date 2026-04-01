from sqlalchemy import Column, Integer, String
from backend.database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    aadhaar = Column(String, unique=True)
    location = Column(String)
    crop_type = Column(String)
    acres = Column(Integer)