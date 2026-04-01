"""
孕期小程序后端主入口
FastAPI 应用配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.auth_routes import router as auth_router
from .api.nutrition_routes import router as nutrition_router
from .api.recipe_routes import router as recipe_router
from .api.family_routes import router as family_router
from .api.record_routes import router as record_router
from .api.recommend_routes import router as recommend_router
from .api.reminder_routes import router as reminder_router
from .api.checkup_routes import router as checkup_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 孕期小程序后端启动...")
    yield
    print("👋 孕期小程序后端关闭...")


app = FastAPI(
    title="孕期小程序 API",
    description="孕期记录与食谱协作小程序后端服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(nutrition_router)
app.include_router(recipe_router)
app.include_router(family_router)
app.include_router(record_router)
app.include_router(recommend_router)
app.include_router(reminder_router)
app.include_router(checkup_router)


@app.get("/")
async def root():
    return {"message": "孕期小程序 API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}