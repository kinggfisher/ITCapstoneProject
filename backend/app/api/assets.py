from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Asset
from app.schemas.schemas import AssetResponse
from typing import List

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/", response_model=List[AssetResponse])
def get_all_assets(db: Session = Depends(get_db)):
    assets = db.query(Asset).all()
    return assets

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset