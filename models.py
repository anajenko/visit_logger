from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)