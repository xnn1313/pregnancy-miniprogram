from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login")
async def login(data: dict):
    return {"token": "xxx", "user": {"id": 1, "name": "妈妈"}}


@router.post("/register")
async def register(data: dict):
    return {"token": "xxx", "user": {"id": 1}}


@router.get("/me")
async def get_me():
    return {"id": 1, "name": "妈妈", "role": "owner"}


@router.post("/logout")
async def logout():
    return {"success": True}