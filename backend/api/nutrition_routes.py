"""
孕期小程序后端 API 路由
提供营养查询、食谱计算等接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from ..services.usda_api import USDAAPIClient, FoodItem
from ..services.nutrition_calculator import NutritionCalculator, Ingredient, RecipeNutrition


router = APIRouter(prefix="/api/v1/nutrition", tags=["营养"])

# 全局客户端（应通过依赖注入管理）
_usda_client: Optional[USDAAPIClient] = None
_calculator: Optional[NutritionCalculator] = None


def get_usda_client() -> USDAAPIClient:
    """获取 USDA 客户端"""
    global _usda_client
    if _usda_client is None:
        _usda_client = USDAAPIClient()
    return _usda_client


def get_calculator() -> NutritionCalculator:
    """获取营养计算器"""
    global _calculator
    if _calculator is None:
        _calculator = NutritionCalculator(get_usda_client())
    return _calculator


# ===== 请求/响应模型 =====

class FoodSearchRequest(BaseModel):
    """食物搜索请求"""
    query: str = Field(..., description="搜索关键词")
    page_size: int = Field(10, ge=1, le=50, description="返回数量")
    language: str = Field("zh", description="语言（zh=中文，en=英文）")


class FoodSearchResponse(BaseModel):
    """食物搜索响应"""
    total: int
    foods: List[Dict]
    
    class Config:
        schema_extra = {
            "example": {
                "total": 10,
                "foods": [
                    {
                        "fdc_id": 171712,
                        "name": "Apples, raw, with skin",
                        "category": "Fruits and Fruit Juices",
                        "nutrients_preview": {
                            "energy": 52,
                            "protein": 0.26
                        }
                    }
                ]
            }
        }


class NutrientDetailResponse(BaseModel):
    """营养详情响应"""
    fdc_id: int
    name: str
    nutrients: Dict[str, Dict]
    
    class Config:
        schema_extra = {
            "example": {
                "fdc_id": 171712,
                "name": "Apples, raw, with skin",
                "nutrients": {
                    "1008": {"name": "能量", "amount": 52, "unit": "kcal"},
                    "1003": {"name": "蛋白质", "amount": 0.26, "unit": "g"}
                }
            }
        }


class RecipeCalculateRequest(BaseModel):
    """菜品营养计算请求"""
    recipe_name: str = Field(..., description="菜品名称")
    ingredients: List[Dict[str, float]] = Field(
        ..., 
        description="食材列表 [{name, amount(g)}]"
    )
    pregnancy_week: int = Field(1, ge=1, le=42, description="孕周")


class RecipeCalculateResponse(BaseModel):
    """菜品营养计算响应"""
    recipe_name: str
    total_weight: float
    nutrients_per_100g: Dict[str, float]
    nutrients_total: Dict[str, float]
    pregnancy_coverage: Dict[str, float]
    nutrient_units: Dict[str, str]
    
    class Config:
        schema_extra = {
            "example": {
                "recipe_name": "番茄炒蛋",
                "total_weight": 315,
                "nutrients_per_100g": {"1008": 145.2},
                "nutrients_total": {"1008": 457.4},
                "pregnancy_coverage": {"1008": 21.7},
                "nutrient_units": {"1008": "kcal"}
            }
        }


class KeyNutrientsResponse(BaseModel):
    """孕期关键营养素列表"""
    nutrients: Dict[str, str]


# ===== API 路由 =====

@router.get("/search", response_model=FoodSearchResponse)
async def search_food(
    query: str = Query(..., description="搜索关键词"),
    page_size: int = Query(10, ge=1, le=50),
    language: str = Query("zh")
):
    """
    搜索食物
    
    - 支持中英文搜索
    - 返回食物基本信息和关键营养素预览
    """
    client = get_usda_client()
    
    try:
        if language == "zh":
            foods = await client.search_by_chinese(query, page_size)
        else:
            foods = await client.search_foods(query, page_size)
        
        # 转换为响应格式
        food_list = []
        for food in foods:
            nutrients_preview = {}
            for code, name in client.KEY_NUTRIENTS.items():
                for n in food.nutrients:
                    if n.code == code:
                        nutrients_preview[name.split()[0]] = n.amount
                        break
            
            food_list.append({
                "fdc_id": food.fdc_id,
                "name": food.name,
                "category": food.category,
                "nutrients_preview": nutrients_preview
            })
        
        return FoodSearchResponse(
            total=len(food_list),
            foods=food_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/food/{fdc_id}", response_model=NutrientDetailResponse)
async def get_food_detail(fdc_id: int):
    """
    获取食物详细营养信息
    
    - 返回所有关键营养素数据
    - 数据以每100g为基准
    """
    client = get_usda_client()
    
    try:
        nutrients = await client.get_nutrients(fdc_id)
        food = await client.get_food_by_id(fdc_id)
        
        nutrients_dict = {}
        for code, info in nutrients.items():
            name = client.KEY_NUTRIENTS.get(code, info.name)
            nutrients_dict[code] = {
                "name": name,
                "amount": info.amount,
                "unit": info.unit
            }
        
        return NutrientDetailResponse(
            fdc_id=fdc_id,
            name=food.name,
            nutrients=nutrients_dict
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/calculate", response_model=RecipeCalculateResponse)
async def calculate_recipe_nutrition(request: RecipeCalculateRequest):
    """
    计算菜品营养
    
    - 输入食材列表和孕周
    - 返回总营养、每100g营养、孕期达标率
    """
    calculator = get_calculator()
    
    try:
        # 构建食材对象
        ingredients = [
            Ingredient(
                name=item.get("name", ""),
                amount=item.get("amount", 0)
            )
            for item in request.ingredients
        ]
        
        # 计算营养
        result = await calculator.calculate_recipe_nutrition(
            recipe_name=request.recipe_name,
            ingredients=ingredients,
            pregnancy_week=request.pregnancy_week
        )
        
        return RecipeCalculateResponse(
            recipe_name=result.recipe_name,
            total_weight=result.total_weight,
            nutrients_per_100g=result.nutrients_per_100g,
            nutrients_total=result.nutrients_total,
            pregnancy_coverage=result.pregnancy_coverage,
            nutrient_units=result.nutrient_units
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/key-nutrients", response_model=KeyNutrientsResponse)
async def get_key_nutrients():
    """
    获取孕期关键营养素列表
    
    - 返回营养素代码和名称映射
    - 用于前端展示
    """
    client = get_usda_client()
    return KeyNutrientsResponse(
        nutrients=client.KEY_NUTRIENTS
    )


# ===== 健康检查 =====

@router.get("/health")
async def health_check():
    """API 健康检查"""
    return {"status": "ok", "service": "nutrition-api"}