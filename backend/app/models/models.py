from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    role = Column(String, default="asset_manager")
    created_at = Column(DateTime, default=datetime.utcnow)

    assessments = relationship("Assessment", back_populates="user")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    location = Column(String)
    max_load_kg = Column(Float, nullable=False)
    material_grade = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    assessments = relationship("Assessment", back_populates="asset")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    load_kg = Column(Float, nullable=False)
    equipment_type = Column(String)
    is_compliant = Column(Boolean, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assessments")
    asset = relationship("Asset", back_populates="assessments")