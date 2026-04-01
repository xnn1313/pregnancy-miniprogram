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
from .services.usda_api import USDAAPIClient
from .db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 孕期小程序后端启动...")
    
    # 初始化数据库
    print("📦 初始化数据库连接...")
    await init_db()
    print("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时清理
    print("👋 孕期小程序后端关闭...")


app = FastAPI(
    title="孕期小程序 API",
    description="孕期记录与食谱协作小程序后端服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置（允许小程序访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://servicewechat.com",  # 微信小程序
        "http://localhost:*",  # 本地开发
    ],
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
    """根路径"""
    return {
        "message": "孕期小程序 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


# 启动命令：uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)