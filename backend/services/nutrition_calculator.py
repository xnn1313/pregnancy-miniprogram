"""
营养计算服务
基于 USDA 数据计算菜品营养含量，支持孕期营养目标对比
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .usda_api import USDAAPIClient, NutrientInfo, FoodItem
import asyncio


@dataclass
class Ingredient:
    """食材"""
    name: str  # 食材名称
    amount: float  # 克数
    fdc_id: Optional[int] = None  # USDA ID（可选）
    nutrients: Dict[str, NutrientInfo] = field(default_factory=dict)  # 营养数据


@dataclass
class RecipeNutrition:
    """菜品营养计算结果"""
    recipe_name: str
    total_weight: float  # 总重量(g)
    nutrients_per_100g: Dict[str, float]  # 每100g营养含量
    nutrients_total: Dict[str, float]  # 总营养含量
    nutrient_units: Dict[str, str]  # 营养素单位
    
    # 孕期关键营养达标率（相对每日推荐摄入量）
    pregnancy_coverage: Dict[str, float] = field(default_factory=dict)


@dataclass
class PregnancyNutrientTarget:
    """孕期营养目标（每日推荐摄入量）"""
    # 孕早/中/晚期不同目标
    trimester: int  # 1/2/3 孕期
    
    # 关键营养素目标（参考中国居民膳食指南）
    targets: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def get_default(cls, trimester: int = 1) -> "PregnancyNutrientTarget":
        """获取默认孕期营养目标"""
        # 孕早期、中期、晚期推荐摄入量
        defaults = {
            1: {  # 孕早期
                "1008": 1800,  # 能量 kcal
                "1003": 55,    # 蛋白质 g
                "1089": 400,   # 叶酸 μg
                "1106": 700,   # 维生素A μg
                "1114": 10,    # 维生素D μg
                "1095": 20,    # 铁 mg
                "1092": 800,   # 钙 mg
                "1098": 11.5,  # 锌 mg
                "1101": 110,   # 碘 μg
                "1087": 25,    # 膳食纤维 g
            },
            2: {  # 孕中期
                "1008": 2100,
                "1003": 70,
                "1089": 400,
                "1106": 770,
                "1114": 10,
                "1095": 24,
                "1092": 1000,
                "1098": 16.5,
                "1101": 110,
                "1087": 28,
            },
            3: {  # 孕晚期
                "1008": 2300,
                "1003": 85,
                "1089": 400,
                "1106": 770,
                "1114": 10,
                "1095": 29,
                "1092": 1000,
                "1098": 16.5,
                "1101": 110,
                "1087": 30,
            }
        }
        
        return cls(
            trimester=trimester,
            targets=defaults.get(trimester, defaults[1])
        )


class NutritionCalculator:
    """营养计算器"""
    
    def __init__(self, usda_client: Optional[USDAAPIClient] = None):
        """
        初始化计算器
        
        Args:
            usda_client: USDA API 客户端（可选，未提供则创建新实例）
        """
        self.usda_client = usda_client or USDAAPIClient()
        self._ingredient_cache: Dict[str, FoodItem] = {}
    
    async def fetch_ingredient_nutrients(
        self,
        ingredient: Ingredient
    ) -> Dict[str, NutrientInfo]:
        """
        获取食材营养数据
        
        Args:
            ingredient: 食材对象
        
        Returns:
            营养数据字典
        """
        # 如果已有 USDA ID，直接获取
        if ingredient.fdc_id:
            return await self.usda_client.get_nutrients(ingredient.fdc_id)
        
        # 否则搜索获取
        foods = await self.usda_client.search_by_chinese(ingredient.name)
        
        if foods:
            # 选择最匹配的第一个
            best_match = foods[0]
            ingredient.fdc_id = best_match.fdc_id
            self._ingredient_cache[ingredient.name] = best_match
            return await self.usda_client.get_nutrients(best_match.fdc_id)
        
        return {}
    
    async def calculate_recipe_nutrition(
        self,
        recipe_name: str,
        ingredients: List[Ingredient],
        pregnancy_week: int = 1
    ) -> RecipeNutrition:
        """
        计算菜品营养
        
        Args:
            recipe_name: 菜品名称
            ingredients: 食材列表
            pregnancy_week: 孕周（用于计算孕期目标）
        
        Returns:
            菜品营养计算结果
        """
        # 计算孕期阶段
        trimester = 1 if pregnancy_week <= 12 else (2 if pregnancy_week <= 27 else 3)
        
        # 获取所有食材营养数据
        for ingredient in ingredients:
            ingredient.nutrients = await self.fetch_ingredient_nutrients(ingredient)
        
        # 计算总重量
        total_weight = sum(i.amount for i in ingredients)
        
        # 计算总营养含量
        total_nutrients: Dict[str, float] = {}
        nutrient_units: Dict[str, str] = {}
        
        for ingredient in ingredients:
            for code, info in ingredient.nutrients.items():
                # 每100g含量 × 实际克数 / 100
                contribution = info.amount * ingredient.amount / 100
                
                if code not in total_nutrients:
                    total_nutrients[code] = 0
                    nutrient_units[code] = info.unit
                
                total_nutrients[code] += contribution
        
        # 计算每100g含量
        nutrients_per_100g = {}
        if total_weight > 0:
            for code, total in total_nutrients.items():
                nutrients_per_100g[code] = total * 100 / total_weight
        
        # 计算孕期营养达标率
        target = PregnancyNutrientTarget.get_default(trimester)
        pregnancy_coverage = {}
        
        for code, target_value in target.targets.items():
            if code in total_nutrients:
                # 该菜品占每日推荐摄入量的百分比
                coverage = (total_nutrients[code] / target_value) * 100
                pregnancy_coverage[code] = min(coverage, 100)  # 上限100%
        
        return RecipeNutrition(
            recipe_name=recipe_name,
            total_weight=total_weight,
            nutrients_per_100g=nutrients_per_100g,
            nutrients_total=total_nutrients,
            nutrient_units=nutrient_units,
            pregnancy_coverage=pregnancy_coverage
        )
    
    def format_nutrition_report(
        self,
        nutrition: RecipeNutrition,
        nutrient_names: Dict[str, str] = None
    ) -> str:
        """
        格式化营养报告
        
        Args:
            nutrition: 营养计算结果
            nutrient_names: 营养素名称映射
        
        Returns:
            格式化文本报告
        """
        names = nutrient_names or self.usda_client.KEY_NUTRIENTS
        
        lines = [
            f"【{nutrition.recipe_name}】营养分析",
            f"总重量：{nutrition.total_weight:.1f}g",
            "",
            "关键营养素（每100g）："
        ]
        
        for code, amount in nutrition.nutrients_per_100g.items():
            if code in names:
                name = names.get(code, code)
                unit = nutrition.nutrient_units.get(code, "")
                lines.append(f"  {name}: {amount:.2f} {unit}")
        
        lines.append("")
        lines.append("孕期营养贡献（占每日推荐）：")
        
        for code, coverage in nutrition.pregnancy_coverage.items():
            if code in names:
                name = names.get(code, code)
                lines.append(f"  {name}: {coverage:.1f}%")
        
        return "\n".join(lines)


# 使用示例
async def example_recipe_calculation():
    """菜品营养计算示例"""
    client = USDAAPIClient(api_key="YOUR_API_KEY")  # 替换为实际 API Key
    calculator = NutritionCalculator(client)
    
    try:
        # 示例：番茄炒蛋
        ingredients = [
            Ingredient(name="鸡蛋", amount=100),  # 2个鸡蛋约100g
            Ingredient(name="西红柿", amount=200),
            Ingredient(name="食用油", amount=15),
        ]
        
        result = await calculator.calculate_recipe_nutrition(
            recipe_name="番茄炒蛋",
            ingredients=ingredients,
            pregnancy_week=15  # 孕中期
        )
        
        print(calculator.format_nutrition_report(result))
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_recipe_calculation())