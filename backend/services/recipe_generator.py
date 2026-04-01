"""
孕期食谱生成模块
基于孕期营养需求生成推荐食谱
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
import json


@dataclass
class PregnancyRecipe:
    """孕期食谱"""
    id: str
    name: str
    trimester: int  # 适用孕期阶段（1/2/3）
    category: str  # 分类：早餐/午餐/晚餐/加餐
    ingredients: List[Dict]  # 食材列表
    steps: List[str]  # 制作步骤
    nutrition_highlight: Dict[str, float]  # 关键营养亮点
    benefits: List[str]  # 孕期益处
    warnings: List[str] = field(default_factory=list)  # 禁忌提示（替代建议）
    prep_time: int = 15  # 准备时间（分钟）
    difficulty: str = "简单"  # 难度


# 孕期禁忌食材库（核心规则）
PREGNANCY_FORBIDDEN = {
    # 高风险禁忌
    "螃蟹": {"level": "high", "reason": "性寒，可能引起宫缩", "weeks": [1, 40], "alternatives": ["鱼肉", "虾"]},
    "甲鱼": {"level": "high", "reason": "性寒，活血化瘀，早期禁忌", "weeks": [1, 12], "alternatives": ["鸡肉"]},
    "薏米": {"level": "high", "reason": "可能诱发流产", "weeks": [1, 12], "alternatives": ["小米", "燕麦"]},
    "马齿苋": {"level": "high", "reason": "性寒滑利，促进宫缩", "weeks": [1, 40], "alternatives": ["菠菜", "苋菜"]},
    "山楂": {"level": "medium", "reason": "促进宫缩，孕早期慎用", "weeks": [1, 12], "alternatives": ["苹果", "橙子"]},
    
    # 中风险禁忌
    "桂圆": {"level": "medium", "reason": "性热，易上火，孕早期慎用", "weeks": [1, 12], "alternatives": ["红枣", "枸杞"]},
    "荔枝": {"level": "medium", "reason": "性热，糖分高", "weeks": [1, 40], "alternatives": ["苹果", "梨"]},
    "木瓜": {"level": "medium", "reason": "含木瓜蛋白酶，孕早期慎用", "weeks": [1, 12], "alternatives": ["香蕉", "芒果"]},
    "芦荟": {"level": "medium", "reason": "可能引起腹泻", "weeks": [1, 40], "alternatives": ["银耳"]},
    
    # 需适量食用
    "西瓜": {"level": "low", "reason": "性寒，适量食用", "weeks": [1, 40], "alternatives": None},
    "冷饮": {"level": "low", "reason": "可能刺激肠胃，适量", "weeks": [1, 40], "alternatives": None},
    "咖啡": {"level": "low", "reason": "每日限200mg咖啡因", "weeks": [1, 40], "alternatives": None},
    "浓茶": {"level": "low", "reason": "影响铁吸收，饭后避免", "weeks": [1, 40], "alternatives": ["淡绿茶", "红枣茶"]},
}


def check_pregnancy_safety(ingredient_name: str, pregnancy_week: int) -> Dict:
    """
    检查食材孕期安全性
    
    Returns:
        {
            "safe": True/False,
            "level": "high/medium/low",
            "reason": str,
            "alternatives": List[str]
        }
    """
    for forbidden_name, rule in PREGNANCY_FORBIDDEN.items():
        if forbidden_name.lower() in ingredient_name.lower():
            # 检查孕周是否在禁忌范围
            min_week, max_week = rule["weeks"]
            if min_week <= pregnancy_week <= max_week:
                return {
                    "safe": False,
                    "level": rule["level"],
                    "reason": rule["reason"],
                    "alternatives": rule.get("alternatives", [])
                }
    
    return {"safe": True, "level": "none", "reason": "", "alternatives": []}


# 首批孕期食谱（50道）
RECIPES_DATABASE = [
    # ===== 孕早期食谱（适合孕1-12周）=====
    # 重点：缓解孕吐、补充叶酸、易消化
    
    PregnancyRecipe(
        id="early-001",
        name="燕麦红枣粥",
        trimester=1,
        category="早餐",
        ingredients=[
            {"name": "燕麦", "amount": 50},
            {"name": "红枣", "amount": 5},
            {"name": "牛奶", "amount": 200},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "燕麦用清水浸泡30分钟",
            "红枣去核切碎",
            "锅中加水，放入燕麦大火煮沸",
            "转小火煮15分钟，加入红枣",
            "加入牛奶，煮5分钟",
            "出锅后加蜂蜜调味"
        ],
        nutrition_highlight={"叶酸": 45, "铁": 3.2, "膳食纤维": 4.5},
        benefits=["缓解孕吐", "补充叶酸", "易消化", "补血养颜"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-002",
        name="蒸蛋羹",
        trimester=1,
        category="早餐",
        ingredients=[
            {"name": "鸡蛋", "amount": 2},
            {"name": "温水", "amount": 100},
            {"name": "盐", "amount": 1},
            {"name": "香油", "amount": 3}
        ],
        steps=[
            "鸡蛋打散，加入温水搅匀",
            "加盐调味，过滤蛋液",
            "蒸锅大火蒸8分钟",
            "出锅淋香油"
        ],
        nutrition_highlight={"蛋白质": 12, "维生素D": 2, "叶酸": 25},
        benefits=["高蛋白易消化", "缓解孕吐", "补充优质蛋白"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-003",
        name="小米南瓜粥",
        trimester=1,
        category="早餐",
        ingredients=[
            {"name": "小米", "amount": 50},
            {"name": "南瓜", "amount": 100},
            {"name": "水", "amount": 500}
        ],
        steps=[
            "南瓜去皮切块蒸熟",
            "小米加水煮粥",
            "南瓜打成泥加入粥中",
            "小火煮10分钟至浓稠"
        ],
        nutrition_highlight={"膳食纤维": 3.5, "维生素A": 120, "叶酸": 30},
        benefits=["养胃易消化", "缓解孕吐", "补充维生素A"],
        prep_time=25,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-004",
        name="清蒸鲈鱼",
        trimester=1,
        category="午餐",
        ingredients=[
            {"name": "鲈鱼", "amount": 300},
            {"name": "姜片", "amount": 10},
            {"name": "葱段", "amount": 15},
            {"name": "蒸鱼豉油", "amount": 15}
        ],
        steps=[
            "鲈鱼洗净，两面划刀",
            "铺姜片葱段",
            "蒸锅大火蒸12分钟",
            "淋蒸鱼豉油即可"
        ],
        nutrition_highlight={"蛋白质": 25, "DHA": 800, "碘": 50},
        benefits=["优质蛋白", "补充DHA促进胎儿脑发育", "低脂健康"],
        prep_time=15,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="early-005",
        name="菠菜豆腐汤",
        trimester=1,
        category="午餐",
        ingredients=[
            {"name": "菠菜", "amount": 150},
            {"name": "豆腐", "amount": 100},
            {"name": "鸡蛋", "amount": 1},
            {"name": "姜片", "amount": 5},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "菠菜焯水切段",
            "豆腐切块",
            "锅中加水煮姜片",
            "加入豆腐煮5分钟",
            "加菠菜，打入蛋花",
            "加盐调味"
        ],
        nutrition_highlight={"叶酸": 150, "钙": 120, "铁": 3.5},
        benefits=["高叶酸", "补钙", "补铁防贫血", "清淡易消化"],
        prep_time=15,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-006",
        name="番茄牛肉面",
        trimester=1,
        category="午餐",
        ingredients=[
            {"name": "牛肉", "amount": 100},
            {"name": "番茄", "amount": 200},
            {"name": "面条", "amount": 150},
            {"name": "青菜", "amount": 50},
            {"name": "姜片", "amount": 5}
        ],
        steps=[
            "牛肉切块焯水",
            "番茄切块炒出汁",
            "加入牛肉炖煮30分钟",
            "面条煮熟",
            "浇上番茄牛肉汤",
            "加青菜即可"
        ],
        nutrition_highlight={"蛋白质": 20, "铁": 5, "维生素C": 30},
        benefits=["补铁补血", "维生素C促进铁吸收", "开胃"],
        prep_time=40,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="early-007",
        name="清炒西蓝花",
        trimester=1,
        category="晚餐",
        ingredients=[
            {"name": "西蓝花", "amount": 200},
            {"name": "蒜末", "amount": 5},
            {"name": "盐", "amount": 2},
            {"name": "食用油", "amount": 10}
        ],
        steps=[
            "西蓝花掰小朵焯水",
            "热油爆香蒜末",
            "下西蓝花翻炒",
            "加盐调味出锅"
        ],
        nutrition_highlight={"叶酸": 100, "维生素C": 50, "膳食纤维": 3},
        benefits=["高叶酸", "抗氧化", "增强免疫力"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-008",
        name="鸡肉粥",
        trimester=1,
        category="晚餐",
        ingredients=[
            {"name": "大米", "amount": 100},
            {"name": "鸡肉", "amount": 100},
            {"name": "姜片", "amount": 5},
            {"name": "青菜", "amount": 50},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "鸡肉切丝焯水",
            "大米加水煮粥",
            "粥煮至浓稠加鸡肉",
            "加青菜、姜片",
            "小火煮10分钟",
            "加盐调味"
        ],
        nutrition_highlight={"蛋白质": 15, "铁": 2, "叶酸": 20},
        benefits=["易消化", "补充优质蛋白", "清淡养胃"],
        prep_time=30,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-009",
        name="酸奶水果杯",
        trimester=1,
        category="加餐",
        ingredients=[
            {"name": "酸奶", "amount": 150},
            {"name": "苹果", "amount": 100},
            {"name": "香蕉", "amount": 50},
            {"name": "蓝莓", "amount": 30}
        ],
        steps=[
            "苹果香蕉切小块",
            "酸奶倒入杯中",
            "铺上水果",
            "点缀蓝莓"
        ],
        nutrition_highlight={"叶酸": 35, "钙": 150, "维生素C": 10},
        benefits=["补钙", "缓解孕吐", "开胃", "益生菌助消化"],
        prep_time=5,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="early-010",
        name="核桃芝麻糊",
        trimester=1,
        category="加餐",
        ingredients=[
            {"name": "核桃", "amount": 30},
            {"name": "黑芝麻", "amount": 20},
            {"name": "糯米粉", "amount": 30},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "核桃芝麻炒香",
            "打成粉末",
            "糯米粉加水煮糊",
            "加入核桃芝麻粉",
            "小火煮5分钟",
            "加蜂蜜调味"
        ],
        nutrition_highlight={"DHA": 300, "钙": 80, "铁": 2},
        benefits=["补脑", "乌发", "补钙", "安神助眠"],
        prep_time=15,
        difficulty="简单"
    ),
    
    # ===== 孕中期食谱（适合孕13-27周）=====
    # 重点：补充铁、钙、蛋白质，胎儿快速发育
    
    PregnancyRecipe(
        id="mid-001",
        name="红枣银耳羹",
        trimester=2,
        category="早餐",
        ingredients=[
            {"name": "银耳", "amount": 20},
            {"name": "红枣", "amount": 10},
            {"name": "枸杞", "amount": 10},
            {"name": "冰糖", "amount": 20}
        ],
        steps=[
            "银耳泡发撕小朵",
            "红枣枸杞洗净",
            "银耳加水炖煮1小时",
            "加红枣枸杞",
            "继续煮20分钟",
            "加冰糖调味"
        ],
        nutrition_highlight={"铁": 3, "维生素C": 20, "膳食纤维": 5},
        benefits=["补血养颜", "润肺", "增强免疫力", "安神"],
        prep_time=90,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-002",
        name="牛奶鸡蛋饼",
        trimester=2,
        category="早餐",
        ingredients=[
            {"name": "面粉", "amount": 100},
            {"name": "鸡蛋", "amount": 1},
            {"name": "牛奶", "amount": 100},
            {"name": "葱花", "amount": 10}
        ],
        steps=[
            "面粉加牛奶调成糊",
            "打入鸡蛋搅匀",
            "加葱花",
            "平底锅摊成薄饼",
            "两面煎金黄"
        ],
        nutrition_highlight={"蛋白质": 15, "钙": 100, "维生素D": 2},
        benefits=["高蛋白", "补钙", "易消化", "能量充足"],
        prep_time=15,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-003",
        name="红烧排骨",
        trimester=2,
        category="午餐",
        ingredients=[
            {"name": "猪排骨", "amount": 300},
            {"name": "生抽", "amount": 20},
            {"name": "老抽", "amount": 10},
            {"name": "姜片", "amount": 10},
            {"name": "八角", "amount": 2}
        ],
        steps=[
            "排骨焯水",
            "热油爆香姜片八角",
            "下排骨翻炒",
            "加生抽老抽",
            "加水炖煮40分钟",
            "大火收汁"
        ],
        nutrition_highlight={"蛋白质": 25, "钙": 80, "铁": 3},
        benefits=["补钙", "补充蛋白质", "胎儿骨骼发育"],
        prep_time=50,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="mid-004",
        name="鲫鱼豆腐汤",
        trimester=2,
        category="午餐",
        ingredients=[
            {"name": "鲫鱼", "amount": 300},
            {"name": "豆腐", "amount": 150},
            {"name": "姜片", "amount": 10},
            {"name": "葱段", "amount": 15},
            {"name": "盐", "amount": 3}
        ],
        steps=[
            "鲫鱼处理干净",
            "热油煎两面金黄",
            "加水、姜片煮开",
            "加入豆腐",
            "小火炖20分钟",
            "加盐调味撒葱段"
        ],
        nutrition_highlight={"蛋白质": 30, "钙": 150, "DHA": 500},
        benefits=["补钙", "促进胎儿脑发育", "优质蛋白"],
        prep_time=30,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="mid-005",
        name="芹菜炒牛肉",
        trimester=2,
        category="晚餐",
        ingredients=[
            {"name": "牛肉", "amount": 150},
            {"name": "芹菜", "amount": 150},
            {"name": "蒜末", "amount": 5},
            {"name": "生抽", "amount": 10},
            {"name": "食用油", "amount": 15}
        ],
        steps=[
            "牛肉切丝用生抽腌制",
            "芹菜切段",
            "热油爆香蒜末",
            "下牛肉快炒",
            "加芹菜翻炒",
            "调味出锅"
        ],
        nutrition_highlight={"铁": 5, "蛋白质": 20, "膳食纤维": 2},
        benefits=["补铁防贫血", "高蛋白", "助消化"],
        prep_time=15,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-006",
        name="牛奶蒸蛋",
        trimester=2,
        category="晚餐",
        ingredients=[
            {"name": "鸡蛋", "amount": 2},
            {"name": "牛奶", "amount": 150},
            {"name": "白糖", "amount": 10}
        ],
        steps=[
            "鸡蛋打散加牛奶",
            "加白糖搅匀",
            "过滤蛋液",
            "蒸锅蒸10分钟",
            "出锅即可"
        ],
        nutrition_highlight={"钙": 180, "蛋白质": 12, "维生素D": 3},
        benefits=["补钙", "优质蛋白", "易消化"],
        prep_time=15,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-007",
        name="紫菜蛋花汤",
        trimester=2,
        category="加餐",
        ingredients=[
            {"name": "紫菜", "amount": 10},
            {"name": "鸡蛋", "amount": 1},
            {"name": "香油", "amount": 5},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "紫菜泡发",
            "锅中加水煮开",
            "下紫菜",
            "打入蛋花",
            "加盐香油调味"
        ],
        nutrition_highlight={"碘": 200, "蛋白质": 6, "铁": 2},
        benefits=["补充碘", "促进胎儿脑发育", "简单快手"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-008",
        name="芝麻糊",
        trimester=2,
        category="加餐",
        ingredients=[
            {"name": "黑芝麻", "amount": 50},
            {"name": "糯米粉", "amount": 30},
            {"name": "白糖", "amount": 20},
            {"name": "牛奶", "amount": 100}
        ],
        steps=[
            "芝麻炒香磨粉",
            "糯米粉加水煮糊",
            "加入芝麻粉",
            "加牛奶搅匀",
            "加白糖调味"
        ],
        nutrition_highlight={"钙": 150, "铁": 5, "维生素E": 3},
        benefits=["补钙", "补血", "乌发养颜"],
        prep_time=15,
        difficulty="简单"
    ),
    
    # ===== 孕晚期食谱（适合孕28-40周）=====
    # 重点：补充铁、膳食纤维，预防贫血和便秘
    
    PregnancyRecipe(
        id="late-001",
        name="红豆薏米粥",
        trimester=3,
        category="早餐",
        ingredients=[
            {"name": "红豆", "amount": 50},
            {"name": "薏米", "amount": 0},  # 薏米孕晚期可用少量，建议替换为小米
            {"name": "小米", "amount": 30},  # 替代薏米
            {"name": "红糖", "amount": 15}
        ],
        steps=[
            "红豆提前浸泡4小时",
            "小米洗净",
            "加水煮粥",
            "小火煮1小时",
            "加红糖调味"
        ],
        nutrition_highlight={"铁": 4, "膳食纤维": 5, "蛋白质": 8},
        benefits=["补血", "消肿", "补充膳食纤维"],
        warnings=["薏米孕早期禁忌，孕晚期可用少量，建议用小米替代"],
        prep_time=70,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-002",
        name="全麦面包配牛油果",
        trimester=3,
        category="早餐",
        ingredients=[
            {"name": "全麦面包", "amount": 100},
            {"name": "牛油果", "amount": 100},
            {"name": "鸡蛋", "amount": 1},
            {"name": "盐", "amount": 1}
        ],
        steps=[
            "鸡蛋煮熟切片",
            "牛油果捣成泥",
            "全麦面包切片",
            "涂抹牛油果泥",
            "铺上鸡蛋片"
        ],
        nutrition_highlight={"膳食纤维": 6, "不饱和脂肪酸": 10, "蛋白质": 10},
        benefits=["补充膳食纤维", "预防便秘", "健康脂肪"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-003",
        name="菠菜猪肝汤",
        trimester=3,
        category="午餐",
        ingredients=[
            {"name": "猪肝", "amount": 100},
            {"name": "菠菜", "amount": 150},
            {"name": "姜片", "amount": 5},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "猪肝切片焯水",
            "菠菜焯水切段",
            "锅中加水姜片煮开",
            "下猪肝煮5分钟",
            "加菠菜",
            "加盐调味"
        ],
        nutrition_highlight={"铁": 25, "叶酸": 100, "维生素A": 500},
        benefits=["高铁补血", "预防贫血", "补充叶酸"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-004",
        name="麻婆豆腐（少辣版）",
        trimester=3,
        category="午餐",
        ingredients=[
            {"name": "豆腐", "amount": 200},
            {"name": "牛肉末", "amount": 50},
            {"name": "豆瓣酱", "amount": 5},  # 少量
            {"name": "花椒粉", "amount": 1},  # 少量
            {"name": "葱花", "amount": 10}
        ],
        steps=[
            "豆腐切块焯水",
            "热油炒牛肉末",
            "加少量豆瓣酱",
            "下豆腐轻轻翻炒",
            "加花椒粉调味",
            "撒葱花出锅"
        ],
        nutrition_highlight={"蛋白质": 15, "钙": 150, "铁": 2},
        benefits=["补钙", "高蛋白", "开胃（少辣）"],
        warnings=["辛辣适量，避免过辣刺激肠胃"],
        prep_time=15,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="late-005",
        name="海带排骨汤",
        trimester=3,
        category="晚餐",
        ingredients=[
            {"name": "排骨", "amount": 300},
            {"name": "海带", "amount": 50},
            {"name": "姜片", "amount": 10},
            {"name": "盐", "amount": 3}
        ],
        steps=[
            "排骨焯水",
            "海带泡发切段",
            "锅中加水姜片",
            "下排骨炖1小时",
            "加海带继续煮20分钟",
            "加盐调味"
        ],
        nutrition_highlight={"碘": 300, "钙": 100, "蛋白质": 20},
        benefits=["补碘", "促进胎儿脑发育", "补钙"],
        prep_time=90,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-006",
        name="燕麦蔬菜粥",
        trimester=3,
        category="晚餐",
        ingredients=[
            {"name": "燕麦", "amount": 80},
            {"name": "胡萝卜", "amount": 50},
            {"name": "青菜", "amount": 50},
            {"name": "鸡蛋", "amount": 1},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "胡萝卜切碎",
            "燕麦加水煮粥",
            "粥煮浓稠加胡萝卜",
            "打入蛋花",
            "加青菜",
            "加盐调味"
        ],
        nutrition_highlight={"膳食纤维": 5, "维生素A": 100, "蛋白质": 8},
        benefits=["预防便秘", "补充膳食纤维", "易消化"],
        prep_time=25,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-007",
        name="香蕉牛奶",
        trimester=3,
        category="加餐",
        ingredients=[
            {"name": "香蕉", "amount": 100},
            {"name": "牛奶", "amount": 200},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "香蕉切片",
            "牛奶加热",
            "香蕉放入牛奶",
            "加蜂蜜调味"
        ],
        nutrition_highlight={"钾": 350, "钙": 200, "膳食纤维": 3},
        benefits=["补充钾", "预防水肿", "助眠", "补钙"],
        prep_time=5,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-008",
        name="核桃酸奶",
        trimester=3,
        category="加餐",
        ingredients=[
            {"name": "核桃", "amount": 30},
            {"name": "酸奶", "amount": 150},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "核桃掰小块",
            "酸奶倒入杯中",
            "撒上核桃",
            "加蜂蜜"
        ],
        nutrition_highlight={"DHA": 300, "钙": 150, "不饱和脂肪酸": 10},
        benefits=["补脑", "补钙", "健康脂肪", "助消化"],
        prep_time=5,
        difficulty="简单"
    ),
    
    # ===== 孕中期补铁补钙新增（8道）=====
    
    PregnancyRecipe(
        id="mid-009",
        name="猪肝菠菜汤",
        trimester=2,
        category="午餐",
        ingredients=[
            {"name": "猪肝", "amount": 100},
            {"name": "菠菜", "amount": 150},
            {"name": "姜片", "amount": 5},
            {"name": "枸杞", "amount": 5},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "猪肝切片用清水浸泡30分钟去血水",
            "菠菜焯水去除草酸，切段备用",
            "锅中加水、姜片煮开",
            "下猪肝片煮至变色",
            "加入菠菜和枸杞",
            "加盐调味，煮2分钟即可"
        ],
        nutrition_highlight={"铁": 22, "叶酸": 120, "维生素A": 4500, "钙": 60},
        benefits=["高效补铁防贫血", "补充叶酸", "维生素A促进铁吸收", "适合孕中期血容量增加需求"],
        warnings=["猪肝含维生素A较高，每周食用不超过2次"],
        prep_time=25,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-010",
        name="黑芝麻糊",
        trimester=2,
        category="早餐",
        ingredients=[
            {"name": "黑芝麻", "amount": 60},
            {"name": "糯米", "amount": 30},
            {"name": "红枣", "amount": 5},
            {"name": "红糖", "amount": 15},
            {"name": "水", "amount": 500}
        ],
        steps=[
            "黑芝麻洗净炒香",
            "糯米提前浸泡2小时",
            "红枣去核切碎",
            "将黑芝麻、糯米、红枣加水打成浆",
            "倒入锅中煮开，不断搅拌",
            "加红糖调味，煮至浓稠"
        ],
        nutrition_highlight={"钙": 280, "铁": 8, "维生素E": 15, "蛋白质": 10},
        benefits=["高钙补铁", "乌发养颜", "润肠通便", "补充维生素E抗氧化"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-011",
        name="虾皮豆腐",
        trimester=2,
        category="午餐",
        ingredients=[
            {"name": "嫩豆腐", "amount": 200},
            {"name": "虾皮", "amount": 30},
            {"name": "葱花", "amount": 10},
            {"name": "生抽", "amount": 10},
            {"name": "食用油", "amount": 15}
        ],
        steps=[
            "豆腐切块焯水去豆腥味",
            "虾皮用清水冲洗沥干",
            "热油爆香葱花",
            "下虾皮翻炒出香味",
            "轻轻放入豆腐块",
            "加生抽调味，小火焖5分钟"
        ],
        nutrition_highlight={"钙": 380, "蛋白质": 18, "碘": 50, "磷": 150},
        benefits=["高钙食品", "补充优质蛋白", "促进胎儿骨骼发育", "虾皮含碘促进脑发育"],
        prep_time=15,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-012",
        name="牛奶炖蛋",
        trimester=2,
        category="早餐",
        ingredients=[
            {"name": "鸡蛋", "amount": 2},
            {"name": "牛奶", "amount": 200},
            {"name": "冰糖", "amount": 15},
            {"name": "枸杞", "amount": 5}
        ],
        steps=[
            "鸡蛋打散加入牛奶搅匀",
            "加入冰糖搅拌至融化",
            "过滤蛋液去除气泡",
            "倒入炖盅，撒上枸杞",
            "隔水炖15分钟",
            "取出即可食用"
        ],
        nutrition_highlight={"钙": 220, "蛋白质": 14, "维生素D": 3, "叶酸": 30},
        benefits=["高钙易吸收", "优质蛋白", "口感嫩滑", "适合孕中期钙需求增加"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-013",
        name="红枣花生汤",
        trimester=2,
        category="加餐",
        ingredients=[
            {"name": "红枣", "amount": 15},
            {"name": "花生", "amount": 50},
            {"name": "红糖", "amount": 20},
            {"name": "水", "amount": 600}
        ],
        steps=[
            "花生提前浸泡2小时",
            "红枣洗净去核",
            "锅中加水，放入花生煮30分钟",
            "加入红枣继续煮20分钟",
            "加红糖调味",
            "煮至花生软烂即可"
        ],
        nutrition_highlight={"铁": 6, "蛋白质": 12, "维生素E": 5, "叶酸": 40},
        benefits=["补血养血", "补充蛋白质", "花生衣有止血作用", "适合孕中期贫血预防"],
        prep_time=60,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-014",
        name="红豆排骨汤",
        trimester=2,
        category="午餐",
        ingredients=[
            {"name": "排骨", "amount": 300},
            {"name": "红豆", "amount": 50},
            {"name": "姜片", "amount": 10},
            {"name": "陈皮", "amount": 3},
            {"name": "盐", "amount": 3}
        ],
        steps=[
            "红豆提前浸泡4小时",
            "排骨焯水去血沫",
            "锅中加水，放入排骨、姜片",
            "大火煮开转小火炖40分钟",
            "加入红豆、陈皮继续炖30分钟",
            "加盐调味"
        ],
        nutrition_highlight={"铁": 5, "蛋白质": 22, "钙": 60, "膳食纤维": 4},
        benefits=["补铁补血", "利水消肿", "补充优质蛋白", "红豆富含叶酸"],
        prep_time=90,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="mid-015",
        name="奶酪土豆泥",
        trimester=2,
        category="晚餐",
        ingredients=[
            {"name": "土豆", "amount": 200},
            {"name": "奶酪", "amount": 30},
            {"name": "牛奶", "amount": 50},
            {"name": "黄油", "amount": 10},
            {"name": "盐", "amount": 1}
        ],
        steps=[
            "土豆去皮切块蒸熟",
            "趁热压成泥",
            "加入黄油拌匀",
            "倒入牛奶搅拌至顺滑",
            "加入奶酪碎",
            "微波炉加热1分钟至奶酪融化"
        ],
        nutrition_highlight={"钙": 180, "蛋白质": 10, "碳水化合物": 35, "维生素B6": 0.5},
        benefits=["高钙补钙", "易消化吸收", "奶酪含优质钙质", "口感顺滑适合孕吐后"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="mid-016",
        name="芝麻核桃糊",
        trimester=2,
        category="加餐",
        ingredients=[
            {"name": "黑芝麻", "amount": 40},
            {"name": "核桃", "amount": 30},
            {"name": "糯米粉", "amount": 20},
            {"name": "蜂蜜", "amount": 15},
            {"name": "水", "amount": 400}
        ],
        steps=[
            "黑芝麻、核桃分别炒香",
            "放入料理机打成细粉",
            "糯米粉加水调成糊",
            "倒入锅中煮开",
            "加入芝麻核桃粉搅匀",
            "加蜂蜜调味，煮至浓稠"
        ],
        nutrition_highlight={"钙": 200, "铁": 6, "DHA": 350, "维生素E": 12},
        benefits=["补钙补铁", "健脑益智", "乌发养颜", "核桃含DHA促进胎儿脑发育"],
        prep_time=20,
        difficulty="简单"
    ),
    
    # ===== 孕晚期预防贫血便秘新增（8道）=====
    
    PregnancyRecipe(
        id="late-009",
        name="红豆小米粥",
        trimester=3,
        category="早餐",
        ingredients=[
            {"name": "红豆", "amount": 40},
            {"name": "小米", "amount": 60},
            {"name": "红糖", "amount": 15},
            {"name": "水", "amount": 600}
        ],
        steps=[
            "红豆提前浸泡4小时",
            "小米洗净",
            "锅中加水，放入红豆煮30分钟",
            "加入小米继续煮30分钟",
            "加红糖调味",
            "煮至软烂浓稠"
        ],
        nutrition_highlight={"铁": 5, "膳食纤维": 4, "蛋白质": 8, "叶酸": 35},
        benefits=["补血养血", "小米养胃安神", "红豆利水消肿", "适合孕晚期水肿"],
        prep_time=70,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-010",
        name="全麦面包三明治",
        trimester=3,
        category="早餐",
        ingredients=[
            {"name": "全麦面包", "amount": 100},
            {"name": "鸡蛋", "amount": 1},
            {"name": "生菜", "amount": 30},
            {"name": "番茄", "amount": 50},
            {"name": "奶酪片", "amount": 20}
        ],
        steps=[
            "鸡蛋煎成荷包蛋",
            "番茄切片",
            "生菜洗净沥干",
            "全麦面包烤至微黄",
            "依次铺上生菜、番茄、鸡蛋、奶酪",
            "盖上另一片面包即可"
        ],
        nutrition_highlight={"膳食纤维": 5, "蛋白质": 12, "钙": 100, "铁": 2},
        benefits=["预防便秘", "高膳食纤维", "营养均衡", "补充能量"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-011",
        name="海带排骨汤",
        trimester=3,
        category="午餐",
        ingredients=[
            {"name": "排骨", "amount": 350},
            {"name": "干海带", "amount": 30},
            {"name": "姜片", "amount": 10},
            {"name": "葱段", "amount": 15},
            {"name": "盐", "amount": 3}
        ],
        steps=[
            "干海带提前泡发洗净",
            "排骨冷水下锅焯水",
            "锅中重新加水，放入排骨、姜片",
            "大火煮开转小火炖1小时",
            "加入海带继续炖30分钟",
            "加盐调味，撒葱段出锅"
        ],
        nutrition_highlight={"碘": 450, "钙": 120, "蛋白质": 25, "铁": 3},
        benefits=["补碘促进胎儿脑发育", "补钙强骨", "海带富含膳食纤维防便秘", "适合孕晚期"],
        prep_time=100,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-012",
        name="紫薯燕麦粥",
        trimester=3,
        category="早餐",
        ingredients=[
            {"name": "紫薯", "amount": 100},
            {"name": "燕麦", "amount": 50},
            {"name": "牛奶", "amount": 200},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "紫薯去皮切小块蒸熟",
            "燕麦加水煮成粥",
            "将蒸熟的紫薯压成泥",
            "加入燕麦粥中搅匀",
            "倒入牛奶煮开",
            "加蜂蜜调味即可"
        ],
        nutrition_highlight={"膳食纤维": 5, "花青素": 50, "钙": 180, "蛋白质": 8},
        benefits=["预防便秘", "花青素抗氧化", "紫薯含丰富膳食纤维", "牛奶补钙"],
        prep_time=25,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-013",
        name="玉米浓汤",
        trimester=3,
        category="午餐",
        ingredients=[
            {"name": "甜玉米", "amount": 150},
            {"name": "牛奶", "amount": 200},
            {"name": "黄油", "amount": 10},
            {"name": "面粉", "amount": 15},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "玉米剥粒，一部分打成玉米浆",
            "热锅融化黄油，炒香面粉",
            "倒入牛奶搅匀",
            "加入玉米粒和玉米浆",
            "小火煮10分钟",
            "加盐调味即可"
        ],
        nutrition_highlight={"膳食纤维": 4, "叶黄素": 200, "钙": 180, "维生素A": 80},
        benefits=["玉米富含叶黄素护眼", "预防便秘", "牛奶补钙", "口感顺滑易消化"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-014",
        name="菠菜猪肝粥",
        trimester=3,
        category="晚餐",
        ingredients=[
            {"name": "大米", "amount": 80},
            {"name": "猪肝", "amount": 80},
            {"name": "菠菜", "amount": 100},
            {"name": "姜片", "amount": 5},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "大米加水煮粥",
            "猪肝切片用清水浸泡去血水",
            "菠菜焯水切碎",
            "粥煮开后加入姜片",
            "放入猪肝片煮至变色",
            "加菠菜碎，加盐调味"
        ],
        nutrition_highlight={"铁": 18, "叶酸": 90, "维生素A": 4000, "蛋白质": 12},
        benefits=["高效补铁防贫血", "补充叶酸", "易消化吸收", "适合孕晚期贫血预防"],
        warnings=["猪肝含维生素A较高，每周不超过2次"],
        prep_time=35,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-015",
        name="红薯银耳羹",
        trimester=3,
        category="晚餐",
        ingredients=[
            {"name": "银耳", "amount": 20},
            {"name": "红薯", "amount": 100},
            {"name": "红枣", "amount": 8},
            {"name": "冰糖", "amount": 20},
            {"name": "水", "amount": 600}
        ],
        steps=[
            "银耳提前泡发撕小朵",
            "红薯去皮切小块",
            "红枣洗净去核",
            "银耳加水炖煮1小时",
            "加入红薯、红枣继续煮20分钟",
            "加冰糖调味"
        ],
        nutrition_highlight={"膳食纤维": 6, "铁": 3, "胶原蛋白": 5, "维生素C": 15},
        benefits=["润肠通便", "银耳润肺", "红薯富含膳食纤维", "适合孕晚期便秘"],
        prep_time=90,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="late-016",
        name="燕麦蔬菜饼",
        trimester=3,
        category="早餐",
        ingredients=[
            {"name": "燕麦", "amount": 80},
            {"name": "胡萝卜", "amount": 50},
            {"name": "西葫芦", "amount": 50},
            {"name": "鸡蛋", "amount": 1},
            {"name": "面粉", "amount": 30},
            {"name": "盐", "amount": 2}
        ],
        steps=[
            "燕麦用水泡软",
            "胡萝卜、西葫芦擦丝",
            "将所有食材混合，加适量水调成糊",
            "平底锅刷油",
            "舀入面糊摊成小饼",
            "两面煎至金黄即可"
        ],
        nutrition_highlight={"膳食纤维": 6, "蛋白质": 8, "维生素A": 100, "β-胡萝卜素": 3},
        benefits=["预防便秘", "高膳食纤维", "蔬菜补充维生素", "低脂健康"],
        prep_time=20,
        difficulty="简单"
    ),
    
    # ===== 各阶段加餐新增（8道）=====
    
    PregnancyRecipe(
        id="snack-001",
        name="坚果酸奶杯",
        trimester=1,
        category="加餐",
        ingredients=[
            {"name": "酸奶", "amount": 150},
            {"name": "混合坚果", "amount": 25},
            {"name": "蜂蜜", "amount": 10},
            {"name": "蓝莓", "amount": 20}
        ],
        steps=[
            "酸奶倒入杯中",
            "坚果切碎",
            "坚果撒在酸奶上",
            "淋上蜂蜜",
            "点缀蓝莓即可"
        ],
        nutrition_highlight={"钙": 150, "不饱和脂肪酸": 8, "维生素E": 5, "蛋白质": 8},
        benefits=["补钙", "坚果补充健康脂肪", "益生菌助消化", "缓解孕吐"],
        prep_time=5,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="snack-002",
        name="水果沙拉",
        trimester=1,
        category="加餐",
        ingredients=[
            {"name": "苹果", "amount": 80},
            {"name": "香蕉", "amount": 60},
            {"name": "橙子", "amount": 80},
            {"name": "酸奶", "amount": 50},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "苹果切块",
            "香蕉切片",
            "橙子去皮掰瓣",
            "所有水果放入碗中",
            "淋上酸奶和蜂蜜"
        ],
        nutrition_highlight={"维生素C": 35, "叶酸": 25, "膳食纤维": 4, "钾": 280},
        benefits=["补充维生素C", "开胃解腻", "补充叶酸", "缓解孕吐"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="snack-003",
        name="香蕉燕麦饼",
        trimester=1,
        category="加餐",
        ingredients=[
            {"name": "香蕉", "amount": 100},
            {"name": "燕麦", "amount": 50},
            {"name": "鸡蛋", "amount": 1},
            {"name": "葡萄干", "amount": 15}
        ],
        steps=[
            "香蕉压成泥",
            "加入燕麦和鸡蛋搅匀",
            "加入葡萄干",
            "平底锅小火加热",
            "舀入面糊摊成小饼",
            "两面煎至金黄"
        ],
        nutrition_highlight={"膳食纤维": 4, "钾": 350, "蛋白质": 6, "碳水化合物": 30},
        benefits=["缓解孕吐", "补充能量", "燕麦富含膳食纤维", "无添加糖更健康"],
        prep_time=15,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="snack-004",
        name="蒸红枣",
        trimester=1,
        category="加餐",
        ingredients=[
            {"name": "红枣", "amount": 15},
            {"name": "水", "amount": 50}
        ],
        steps=[
            "红枣洗净",
            "放入蒸碗",
            "加少量水",
            "蒸锅大火蒸15分钟",
            "趁热食用"
        ],
        nutrition_highlight={"铁": 4, "维生素C": 30, "叶酸": 20, "蛋白质": 2},
        benefits=["补血养血", "补充铁元素", "蒸制更易消化", "适合孕早期补血"],
        warnings=["红枣含糖较高，每日适量食用"],
        prep_time=20,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="snack-005",
        name="牛奶木瓜",
        trimester=2,
        category="加餐",
        ingredients=[
            {"name": "木瓜", "amount": 150},
            {"name": "牛奶", "amount": 200},
            {"name": "蜂蜜", "amount": 10}
        ],
        steps=[
            "木瓜去皮去籽切块",
            "牛奶加热至温热",
            "木瓜放入碗中",
            "倒入温牛奶",
            "淋蜂蜜即可"
        ],
        nutrition_highlight={"维生素C": 50, "钙": 200, "β-胡萝卜素": 300, "叶酸": 30},
        benefits=["补充维生素C", "牛奶补钙", "木瓜助消化", "口感清甜"],
        warnings=["木瓜孕早期慎用，孕中期后可适量食用"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="snack-006",
        name="核桃芝麻丸",
        trimester=2,
        category="加餐",
        ingredients=[
            {"name": "核桃", "amount": 50},
            {"name": "黑芝麻", "amount": 30},
            {"name": "蜂蜜", "amount": 30},
            {"name": "红枣碎", "amount": 20}
        ],
        steps=[
            "核桃炒香打碎",
            "黑芝麻炒香",
            "核桃碎、芝麻、红枣碎混合",
            "加入蜂蜜拌匀",
            "搓成小丸（约10克一个）",
            "冷藏保存"
        ],
        nutrition_highlight={"钙": 120, "DHA": 400, "铁": 4, "维生素E": 8},
        benefits=["补脑益智", "补钙补铁", "方便携带", "适合随时补充能量"],
        prep_time=25,
        difficulty="中等"
    ),
    
    PregnancyRecipe(
        id="snack-007",
        name="水果拼盘",
        trimester=3,
        category="加餐",
        ingredients=[
            {"name": "苹果", "amount": 60},
            {"name": "梨", "amount": 60},
            {"name": "葡萄", "amount": 50},
            {"name": "猕猴桃", "amount": 50},
            {"name": "圣女果", "amount": 40}
        ],
        steps=[
            "苹果、梨切块",
            "葡萄洗净对半切",
            "猕猴桃切片",
            "圣女果洗净",
            "所有水果摆盘即可"
        ],
        nutrition_highlight={"维生素C": 45, "膳食纤维": 5, "叶酸": 25, "钾": 300},
        benefits=["补充维生素", "预防便秘", "多种水果营养均衡", "清爽开胃"],
        prep_time=10,
        difficulty="简单"
    ),
    
    PregnancyRecipe(
        id="snack-008",
        name="酸奶慕斯",
        trimester=3,
        category="加餐",
        ingredients=[
            {"name": "酸奶", "amount": 150},
            {"name": "淡奶油", "amount": 50},
            {"name": "吉利丁片", "amount": 5},
            {"name": "蜂蜜", "amount": 15},
            {"name": "草莓", "amount": 30}
        ],
        steps=[
            "吉利丁片冷水泡软",
            "淡奶油打发至六成",
            "酸奶与蜂蜜混合",
            "吉利丁隔水融化后加入酸奶",
            "拌入淡奶油",
            "倒入模具冷藏2小时，点缀草莓"
        ],
        nutrition_highlight={"钙": 180, "蛋白质": 8, "维生素C": 15, "益生菌": 10},
        benefits=["补钙", "益生菌助消化", "口感顺滑", "适合孕晚期食欲不振"],
        prep_time=20,
        difficulty="中等"
    ),
]


def get_recipes_by_trimester(trimester: int) -> List[PregnancyRecipe]:
    """按孕期阶段获取食谱"""
    return [r for r in RECIPES_DATABASE if r.trimester == trimester]


def get_recipes_by_category(category: str) -> List[PregnancyRecipe]:
    """按分类获取食谱"""
    return [r for r in RECIPES_DATABASE if r.category == category]


def search_recipe(query: str) -> List[PregnancyRecipe]:
    """搜索食谱"""
    query_lower = query.lower()
    return [
        r for r in RECIPES_DATABASE 
        if query_lower in r.name.lower() or 
        any(query_lower in i["name"].lower() for i in r.ingredients)
    ]


def recipe_to_dict(recipe: PregnancyRecipe) -> Dict:
    """食谱转字典"""
    return {
        "id": recipe.id,
        "name": recipe.name,
        "trimester": recipe.trimester,
        "category": recipe.category,
        "ingredients": recipe.ingredients,
        "steps": recipe.steps,
        "nutrition_highlight": recipe.nutrition_highlight,
        "benefits": recipe.benefits,
        "warnings": recipe.warnings,
        "prep_time": recipe.prep_time,
        "difficulty": recipe.difficulty
    }


def export_recipes_json() -> str:
    """导出所有食谱为JSON"""
    recipes_dict = [recipe_to_dict(r) for r in RECIPES_DATABASE]
    return json.dumps(recipes_dict, ensure_ascii=False, indent=2)


# 统计信息
def get_stats():
    """获取食谱库统计"""
    return {
        "total": len(RECIPES_DATABASE),
        "by_trimester": {
            "孕早期": len(get_recipes_by_trimester(1)),
            "孕中期": len(get_recipes_by_trimester(2)),
            "孕晚期": len(get_recipes_by_trimester(3))
        },
        "by_category": {
            "早餐": len(get_recipes_by_category("早餐")),
            "午餐": len(get_recipes_by_category("午餐")),
            "晚餐": len(get_recipes_by_category("晚餐")),
            "加餐": len(get_recipes_by_category("加餐"))
        }
    }


# 导出常量供外部使用
__all__ = [
    "PregnancyRecipe",
    "RECIPES_DATABASE",
    "PREGNANCY_FORBIDDEN",
    "get_recipes_by_trimester",
    "get_recipes_by_category",
    "search_recipe",
    "recipe_to_dict",
    "export_recipes_json",
    "get_stats",
    "check_pregnancy_safety",
]


if __name__ == "__main__":
    # 打印统计
    stats = get_stats()
    print("=== 孕期食谱库统计 ===")
    print(f"总数: {stats['total']} 道")
    print("\n按孕期阶段:")
    for k, v in stats["by_trimester"].items():
        print(f"  {k}: {v} 道")
    print("\n按分类:")
    for k, v in stats["by_category"].items():
        print(f"  {k}: {v} 道")
    
    # 示例：孕早期早餐
    print("\n=== 孕早期早餐示例 ===")
    early_breakfast = [r for r in get_recipes_by_trimester(1) if r.category == "早餐"]
    for r in early_breakfast[:3]:
        print(f"- {r.name}")
        print(f"  关键营养: {r.nutrition_highlight}")
        print(f"  益处: {', '.join(r.benefits)}")
        print()