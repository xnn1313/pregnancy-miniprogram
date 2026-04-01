"""
USDA FoodData Central API 对接模块
用于获取食物营养数据，支持孕期小程序营养计算

API 文档：https://api.nal.usda.gov/fdc/v1/
申请 API Key：https://fdc.nal.usda.gov/api-key-sign-up.html
"""

import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os


@dataclass
class NutrientInfo:
    """营养成分信息"""
    name: str
    amount: float  # 每100g含量
    unit: str
    code: str  # USDA营养素代码
    
    @classmethod
    def from_usda(cls, data: Dict) -> "NutrientInfo":
        """从 USDA API 数据构建"""
        return cls(
            name=data.get("nutrientName", ""),
            amount=data.get("value", 0),
            unit=data.get("unitName", ""),
            code=str(data.get("nutrientNumber", ""))
        )


@dataclass
class FoodItem:
    """食物项"""
    fdc_id: int
    name: str
    category: str
    nutrients: List[NutrientInfo]
    description: Optional[str] = None
    data_source: str = "USDA"
    
    @classmethod
    def from_usda(cls, data: Dict) -> "FoodItem":
        """从 USDA API 数据构建"""
        nutrients = [
            NutrientInfo.from_usda(n) 
            for n in data.get("foodNutrients", [])
        ]
        return cls(
            fdc_id=data.get("fdcId", 0),
            name=data.get("description", ""),
            category=data.get("foodCategory", ""),
            nutrients=nutrients,
            description=data.get("additionalDescriptions"),
            data_source="USDA"
        )


class USDAAPIClient:
    """USDA FoodData Central API 客户端"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    # 常用营养素代码（孕期关键营养）
    KEY_NUTRIENTS = {
        "1008": "能量 (kcal)",
        "1003": "脂肪 (g)",
        "1004": "碳水化合物 (g)",
        "1005": "蛋白质 (g)",
        "1089": "叶酸 (μg)",
        "1106": "维生素A (μg)",
        "1114": "维生素D (μg)",
        "1095": "铁 (mg)",
        "1092": "钙 (mg)",
        "1098": "锌 (mg)",
        "1101": "碘 (μg)",
        "1087": "膳食纤维 (g)",
    }
    
    # 缓存过期时间（秒）
    CACHE_EXPIRE = 3600 * 24  # 24小时
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: USDA API Key（可从环境变量读取）
        """
        self.api_key = api_key or os.getenv("USDA_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._cache: Dict[str, Any] = {}
        
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry["expire"]:
                return entry["data"]
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        self._cache[key] = {
            "data": data,
            "expire": datetime.now() + timedelta(seconds=self.CACHE_EXPIRE)
        }
    
    async def search_foods(
        self,
        query: str,
        page_size: int = 10,
        page_number: int = 1,
        data_type: Optional[List[str]] = None
    ) -> List[FoodItem]:
        """
        搜索食物
        
        Args:
            query: 搜索关键词（如 "apple", "rice"）
            page_size: 返回数量
            page_number: 页码
            data_type: 数据类型过滤
                - "Foundation" - 基础食物数据（推荐）
                - "SR Legacy" - 传统标准参考数据
                - "Branded" - 品牌食品
                - "Survey (FNDDS)" - 调查数据
        
        Returns:
            食物列表
        """
        cache_key = f"search:{query}:{page_size}:{page_number}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "pageNumber": page_number,
            "sortBy": "description.lowercase",
            "sortOrder": "asc"
        }
        
        if data_type:
            params["dataType"] = data_type
        
        url = f"{self.BASE_URL}/foods/search"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        foods = [
            FoodItem.from_usda(item) 
            for item in data.get("foods", [])
        ]
        
        self._set_cache(cache_key, foods)
        return foods
    
    async def get_food_by_id(self, fdc_id: int) -> FoodItem:
        """
        获取单个食物详情
        
        Args:
            fdc_id: USDA FoodData Central ID
        
        Returns:
            食物详情
        """
        cache_key = f"food:{fdc_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        params = {"api_key": self.api_key}
        url = f"{self.BASE_URL}/foods/{fdc_id}"
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        food = FoodItem.from_usda(response.json())
        self._set_cache(cache_key, food)
        return food
    
    async def get_nutrients(
        self,
        fdc_id: int,
        nutrient_codes: Optional[List[str]] = None
    ) -> Dict[str, NutrientInfo]:
        """
        获取指定营养素数据
        
        Args:
            fdc_id: 食物ID
            nutrient_codes: 营养素代码列表（默认返回孕期关键营养素）
        
        Returns:
            营养素字典 {代码: NutrientInfo}
        """
        food = await self.get_food_by_id(fdc_id)
        
        codes = nutrient_codes or list(self.KEY_NUTRIENTS.keys())
        result = {}
        
        for nutrient in food.nutrients:
            if nutrient.code in codes:
                result[nutrient.code] = nutrient
        
        return result
    
    async def search_by_chinese(
        self,
        chinese_name: str,
        english_mapping: Optional[Dict[str, str]] = None
    ) -> List[FoodItem]:
        """
        中文名称搜索（需要翻译映射）
        
        Args:
            chinese_name: 中文食物名称
            english_mapping: 中文名到英文名的映射字典
        
        Returns:
            食物列表
        
        Note:
            USDA 不支持中文搜索，需要先翻译或使用预设映射表
        """
        # 默认常见食物映射
        default_mapping = {
            "苹果": "apple",
            "香蕉": "banana",
            "鸡蛋": "egg",
            "牛奶": "milk",
            "牛肉": "beef",
            "猪肉": "pork",
            "鸡肉": "chicken",
            "鱼": "fish",
            "虾": "shrimp",
            "米饭": "rice",
            "面条": "noodle",
            "豆腐": "tofu",
            "菠菜": "spinach",
            "胡萝卜": "carrot",
            "西红柿": "tomato",
            "黄瓜": "cucumber",
            "白菜": "cabbage",
            "土豆": "potato",
            "红薯": "sweet potato",
            "燕麦": "oat",
            "核桃": "walnut",
            "花生": "peanut",
            "豆腐": "tofu",
            "豆浆": "soymilk",
            "酸奶": "yogurt",
            "奶酪": "cheese",
            "面包": "bread",
            "玉米": "corn",
            "西瓜": "watermelon",
            "橙子": "orange",
            "葡萄": "grape",
            "草莓": "strawberry",
            "蓝莓": "blueberry",
            "芒果": "mango",
            "猕猴桃": "kiwi",
            "樱桃": "cherry",
            "柠檬": "lemon",
        }
        
        mapping = english_mapping or default_mapping
        english_name = mapping.get(chinese_name, chinese_name)
        
        return await self.search_foods(
            query=english_name,
            data_type=["Foundation", "SR Legacy"]
        )
    
    def get_key_nutrient_names(self) -> Dict[str, str]:
        """获取孕期关键营养素列表"""
        return self.KEY_NUTRIENTS.copy()


# 同步版本（用于简单场景）
class USDAAPIClientSync:
    """USDA API 同步客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("USDA_API_KEY", "")
        self.client = httpx.Client(timeout=30.0)
    
    def search_foods(self, query: str, page_size: int = 10) -> List[FoodItem]:
        """同步搜索"""
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": ["Foundation", "SR Legacy"]
        }
        
        response = self.client.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params=params
        )
        response.raise_for_status()
        
        return [
            FoodItem.from_usda(item) 
            for item in response.json().get("foods", [])
        ]
    
    def get_food_by_id(self, fdc_id: int) -> FoodItem:
        """同步获取详情"""
        response = self.client.get(
            f"https://api.nal.usda.gov/fdc/v1/foods/{fdc_id}",
            params={"api_key": self.api_key}
        )
        response.raise_for_status()
        return FoodItem.from_usda(response.json())


# 使用示例
async def example_usage():
    """使用示例"""
    client = USDAAPIClient()
    
    try:
        # 搜索食物
        foods = await client.search_foods("apple", page_size=5)
        print(f"找到 {len(foods)} 个苹果相关食物")
        
        for food in foods[:3]:
            print(f"- {food.name} (ID: {food.fdc_id})")
        
        # 获取详细营养数据
        if foods:
            apple = foods[0]
            nutrients = await client.get_nutrients(apple.fdc_id)
            
            print("\n苹果关键营养素（每100g）：")
            for code, info in nutrients.items():
                print(f"- {info.name}: {info.amount} {info.unit}")
        
        # 中文搜索
        chinese_foods = await client.search_by_chinese("菠菜")
        print(f"\n找到 {len(chinese_foods)} 个菠菜相关食物")
        
    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())