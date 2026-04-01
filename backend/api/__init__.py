"""API 路由包"""
from .nutrition_routes import router as nutrition_router
from .recipe_routes import router as recipe_router

__all__ = ["nutrition_router", "recipe_router"]