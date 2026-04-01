from sqlalchemy import Column, Integer, Float, DateTime
from datetime import datetime
from backend.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    humidity = Column(Float)
    moisture = Column(Float)
    temperature = Column(Float)
    ph = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
