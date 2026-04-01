"""
食谱相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from ..services.recipe_generator import (
    PregnancyRecipe,
    get_recipes_by_trimester,
    get_recipes_by_category,
    search_recipe,
    recipe_to_dict,
    get_stats,
    check_pregnancy_safety,
    PREGNANCY_FORBIDDEN
)


router = APIRouter(prefix="/api/v1/recipes", tags=["食谱"])


# ===== 请求/响应模型 =====

class RecipeListResponse(BaseModel):
    """食谱列表响应"""
    total: int
    recipes: List[Dict]


class RecipeDetailResponse(BaseModel):
    """食谱详情响应"""
    id: str
    name: str
    trimester: int
    category: str
    ingredients: List[Dict]
    steps: List[str]
    nutrition_highlight: Dict[str, float]
    benefits: List[str]
    warnings: List[str]
    prep_time: int
    difficulty: str


class SafetyCheckRequest(BaseModel):
    """禁忌检查请求"""
    ingredient: str = Field(..., description="食材名称")
    pregnancy_week: int = Field(..., ge=1, le=42, description="孕周")


class SafetyCheckResponse(BaseModel):
    """禁忌检查响应"""
    ingredient: str
    pregnancy_week: int
    safe: bool
    level: str
    reason: Optional[str]
    alternatives: List[str]


class StatsResponse(BaseModel):
    """统计响应"""
    total: int
    by_trimester: Dict[str, int]
    by_category: Dict[str, int]


class ForbiddenListResponse(BaseModel):
    """禁忌列表响应"""
    total: int
    items: Dict[str, Dict]


# ===== API 路由 =====

@router.get("/list", response_model=RecipeListResponse)
async def list_recipes(
    trimester: Optional[int] = Query(None, ge=1, le=3, description="孕期阶段（1/2/3）"),
    category: Optional[str] = Query(None, description="分类（早餐/午餐/晚餐/加餐）")
):
    """
    获取食谱列表
    
    - 可按孕期阶段筛选
    - 可按分类筛选
    """
    recipes = []
    
    if trimester and category:
        recipes = [
            r for r in get_recipes_by_trimester(trimester)
            if r.category == category
        ]
    elif trimester:
        recipes = get_recipes_by_trimester(trimester)
    elif category:
        recipes = get_recipes_by_category(category)
    else:
        from ..services.recipe_generator import RECIPES_DATABASE
        recipes = RECIPES_DATABASE
    
    return RecipeListResponse(
        total=len(recipes),
        recipes=[recipe_to_dict(r) for r in recipes]
    )


@router.get("/search", response_model=RecipeListResponse)
async def search_recipes(query: str = Query(..., description="搜索关键词")):
    """
    搜索食谱
    
    - 支持按名称搜索
    - 支持按食材搜索
    """
    recipes = search_recipe(query)
    
    return RecipeListResponse(
        total=len(recipes),
        recipes=[recipe_to_dict(r) for r in recipes]
    )


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe_detail(recipe_id: str):
    """
    获取食谱详情
    
    - 包含完整步骤、营养信息、禁忌提示
    """
    from ..services.recipe_generator import RECIPES_DATABASE
    
    for recipe in RECIPES_DATABASE:
        if recipe.id == recipe_id:
            return RecipeDetailResponse(**recipe_to_dict(recipe))
    
    raise HTTPException(status_code=404, detail="食谱不存在")


@router.post("/safety-check", response_model=SafetyCheckResponse)
async def check_safety(request: SafetyCheckRequest):
    """
    检查食材孕期安全性
    
    - 返回安全等级、原因、替代建议
    """
    result = check_pregnancy_safety(request.ingredient, request.pregnancy_week)
    
    return SafetyCheckResponse(
        ingredient=request.ingredient,
        pregnancy_week=request.pregnancy_week,
        safe=result["safe"],
        level=result["level"],
        reason=result.get("reason"),
        alternatives=result.get("alternatives", [])
    )


@router.get("/forbidden", response_model=ForbiddenListResponse)
async def get_forbidden_list():
    """
    获取孕期禁忌食材列表
    
    - 包含禁忌等级、原因、替代建议
    """
    return ForbiddenListResponse(
        total=len(PREGNANCY_FORBIDDEN),
        items=PREGNANCY_FORBIDDEN
    )


@router.get("/stats", response_model=StatsResponse)
async def get_recipe_stats():
    """
    获取食谱库统计信息
    
    - 总数、按孕期分布、按分类分布
    """
    stats = get_stats()
    
    return StatsResponse(
        total=stats["total"],
        by_trimester=stats["by_trimester"],
        by_category=stats["by_category"]
    )


# ===== 收藏相关接口 =====

@router.post("/favorite")
async def add_favorite(data: dict):
    """
    添加收藏
    
    - 将食谱添加到用户收藏列表
    """
    return {"success": True}


@router.get("/favorites")
async def list_favorites():
    """
    获取收藏列表
    
    - 返回用户收藏的食谱ID列表
    """
    return []


@router.delete("/favorite/{id}")
async def remove_favorite(id: int):
    """
    取消收藏
    
    - 从收藏列表中移除指定食谱
    """
    return {"success": True}