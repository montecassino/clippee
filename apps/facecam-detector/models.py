from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Clip(Base):
    __tablename__ = "Clip"

    id = Column(String(36), primary_key=True) 
    videoPath = Column(String(255), nullable=False)
    
    faceCamX = Column(Float, nullable=False)
    faceCamY = Column(Float, nullable=False)
    faceCamWidth = Column(Float, nullable=False)
    faceCamHeight = Column(Float, nullable=False)
    
    clipStartTimestamp = Column(Float, nullable=False)
    clipEndTimestamp = Column(Float, nullable=False)
    
    status = Column(String(20), default="DRAFT") 
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())