"""
数据库连接配置
支持异步 PostgreSQL 连接
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 从环境变量获取数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/pregnancy_db"
)

# 同步数据库 URL（用于 Alembic 迁移等）
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")


class Base(DeclarativeBase):
    """SQLAlchemy 声明基类"""
    pass


# 异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# 异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    获取数据库会话（依赖注入用）
    使用方式：
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库（创建所有表）
    生产环境建议使用 Alembic 迁移
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 同步引擎和会话（用于 Alembic 等工具）
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
sync_session_maker = sessionmaker(bind=sync_engine)