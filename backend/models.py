from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from backend.database import Base


class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    service = Column(String(120), nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Новий")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
