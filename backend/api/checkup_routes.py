from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/checkup", tags=["产检"])


@router.post("/plan")
async def create_plan(data: dict):
    return {"id": 1}


@router.get("/plans")
async def list_plans():
    return []


@router.post("/result")
async def add_result(data: dict):
    return {"id": 1}


@router.get("/timeline")
async def get_timeline():
    return []