from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from backend.database import Base

class PestHistory(Base):
    __tablename__ = "pest_history"

    id = Column(Integer, primary_key=True, index=True)
    pest = Column(String)
    confidence = Column(Float)
    advice = Column(String)
    image_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)