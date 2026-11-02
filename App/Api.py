
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIRECTORY = Path(__file__).resolve().parent

sys.path.insert(0, str(APP_DIRECTORY))

from AssetManager import AssetManager

DATABASE_PATH = PROJECT_ROOT / "VillageAssets.db"

app = FastAPI(
    title="Village Asset Mapping API",
    description="API for village asset mapping and service-gap analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Request model for adding an asset
class AssetCreate(BaseModel):
    name: str
    village: str
    category: str
    latitude: float
    longitude: float
    owner_type: str
    owner_name: str
    managing_authority: str | None = None
    verification_status: str = "unverified"


def get_asset_manager():
    return AssetManager(str(DATABASE_PATH))


@app.get("/")
def home():
    return {
        "message": "Village Asset Mapping API is running.",
        "status": "success",
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "database": "SQLite"}


@app.get("/api/assets")
def get_all_assets():
    manager = get_asset_manager()
    try:
        assets = manager.list_assets()
        return {"total": len(assets), "assets": assets}
    finally:
        manager.close()


@app.get("/api/assets/{asset_id}")
def get_asset_by_id(asset_id: str):
    manager = get_asset_manager()
    try:
        asset = manager.get_asset(asset_id)
        if asset is None:
            raise HTTPException(
                status_code=404,
                detail="Asset not found."
            )
        return asset
    finally:
        manager.close()


@app.get("/api/search")
def search_assets(q: str):
    manager = get_asset_manager()
    try:
        results = manager.search_assets(q)
        return {
            "query": q,
            "total": len(results),
            "results": results,
        }
    finally:
        manager.close()


# Add a new asset
@app.post("/api/assets", status_code=201)
def create_asset(asset_data: AssetCreate):
    manager = get_asset_manager()

    try:
        result = manager.add_asset(
            name=asset_data.name,
            village=asset_data.village,
            category=asset_data.category,
            latitude=asset_data.latitude,
            longitude=asset_data.longitude,
            owner_type=asset_data.owner_type,
            owner_name=asset_data.owner_name,
            managing_authority=asset_data.managing_authority,
            verification_status=asset_data.verification_status,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["errors"],
            )

        return {
            "message": "Asset added successfully.",
            "asset": result["asset"],
        }

    finally:
        manager.close()
