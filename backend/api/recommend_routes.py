from fastapi import APIRouter
from ..services.recommendation_engine import get_recommendations

router = APIRouter(prefix="/api/v1/recommend", tags=["推荐"])

@router.get("/today")
async def today(week: int = 15):
    return get_recommendations(week)