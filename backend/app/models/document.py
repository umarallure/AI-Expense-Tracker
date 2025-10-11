from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid

class Document(Base):
    __tablename__ = 'documents'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False)
    project_division_id = Column(String, ForeignKey('project_divisions.id'), nullable=True)
    document_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="documents")
    business = relationship("Business", back_populates="documents")
    project_division = relationship("ProjectDivision", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, type={self.document_type}, user_id={self.user_id})>"