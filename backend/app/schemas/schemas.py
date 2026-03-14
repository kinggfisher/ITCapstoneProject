from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

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