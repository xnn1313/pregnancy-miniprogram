from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/reminder", tags=["提醒"])

@router.post("/task")
async def create_task(data: dict):
    return {"id": 1}

@router.get("/tasks")
async def list_tasks():
    return []

@router.put("/task/{id}")
async def update_task(id: int, data: dict):
    return {"success": True}

@router.delete("/task/{id}")
async def delete_task(id: int):
    return {"success": True}