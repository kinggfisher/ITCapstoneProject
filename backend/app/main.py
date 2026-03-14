from fastapi import FastAPI
from app.database import engine
from app.models import models
from app.api import assets

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AssetGuard AI")

app.include_router(assets.router)

@app.get("/")
def root():
    return {"message": "AssetGuard API is running"}