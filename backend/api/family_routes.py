from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/family", tags=["家庭"])

@router.post("/archive")
async def create_archive(data: dict):
    return {"id": 1}

@router.get("/archive")
async def get_archive():
    return {"due_date": "2026-07-15", "week": 15}

@router.post("/member")
async def invite_member(data: dict):
    return {"id": 1}

@router.get("/members")
async def list_members():
    return [{"role": "owner", "name": "妈妈"}]