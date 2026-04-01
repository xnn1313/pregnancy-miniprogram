# 孕期小程序后端

基于 FastAPI 的营养查询与计算服务。

## 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env，填写 USDA API Key
# 申请地址：https://fdc.nal.usda.gov/api-key-sign-up.html
```

### 3. 启动服务

```bash
uvicorn main:app --reload --port 8000
```

## API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 核心 API

### 搜索食物
```
GET /api/v1/nutrition/search?query=苹果&page_size=10&language=zh
```

### 获取营养详情
```
GET /api/v1/nutrition/food/{fdc_id}
```

### 计算菜品营养
```
POST /api/v1/nutrition/calculate
{
  "recipe_name": "番茄炒蛋",
  "ingredients": [
    {"name": "鸡蛋", "amount": 100},
    {"name": "西红柿", "amount": 200}
  ],
  "pregnancy_week": 15
}
```

### 孕期关键营养素
```
GET /api/v1/nutrition/key-nutrients
```

## 项目结构

```
backend/
├── main.py              # FastAPI 主入口
├── api/
│   ├── __init__.py
│   └── nutrition_routes.py  # API 路由
├── services/
│   ├── __init__.py
│   ├── usda_api.py          # USDA API 对接
│   └── nutrition_calculator.py  # 营养计算
├── requirements.txt     # 依赖列表
└── .env.example         # 配置示例
```

## 孕期关键营养素

| 营养素 | 孕早期 | 孕中期 | 孕晚期 |
|--------|--------|--------|--------|
| 能量 | 1800 kcal | 2100 kcal | 2300 kcal |
| 蛋白质 | 55g | 70g | 85g |
| 叶酸 | 400μg | 400μg | 400μg |
| 铁 | 20mg | 24mg | 29mg |
| 钙 | 800mg | 1000mg | 1000mg |

## TODO

- [ ] 数据库集成（PostgreSQL）
- [ ] Redis 缓存
- [ ] 中国食物成分表数据
- [ ] 食谱库管理 API
- [ ] 孕期禁忌校验 API