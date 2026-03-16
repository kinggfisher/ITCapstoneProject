from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class AssessmentCreate(BaseModel):
    asset_id: UUID
    load_kg: float
    equipment_type: str
    notes: str | None

class AssetResponse(BaseModel):
    id: UUID
    name: str
    location: str | None
    max_load_kg: float
    material_grade: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True

        