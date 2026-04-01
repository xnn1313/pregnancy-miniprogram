from fastapi import APIRouter
from datetime import date

router = APIRouter(prefix="/api/v1/record", tags=["记录"])


@router.post("/")
async def save_record(data: dict):
    return {"success": True, "date": str(date.today())}


@router.get("/today")
async def get_today():
    return {"weight": 60, "symptoms": [], "mood": "good"}


@router.get("/history")
async def get_history(page: int = 1):
    return {"records": [], "total": 0}