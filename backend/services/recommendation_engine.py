def get_recommendations(week: int, symptoms: list = None):
    trimester = 1 if week <= 12 else (2 if week <= 27 else 3)
    return {
        "breakfast": {"name": "燕麦红枣粥", "reason": "补充叶酸"},
        "lunch": {"name": "清蒸鲈鱼", "reason": "优质蛋白"},
        "dinner": {"name": "菠菜豆腐汤", "reason": "补铁补钙"},
        "snacks": [{"name": "酸奶水果杯", "reason": "开胃"}]
    }