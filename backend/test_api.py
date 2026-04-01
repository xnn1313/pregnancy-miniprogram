"""USDA API 连接测试"""

import asyncio
import httpx


async def test_usda_api():
    """测试 USDA API 连接"""
    api_key = "5cjA9e29Dbd0h1CTOg1AAujvCujUICMlUHslIC3x"
    
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # 测试搜索苹果
        params = {
            "api_key": api_key,
            "query": "apple",
            "pageSize": 3,
            "dataType": ["Foundation", "SR Legacy"]
        }
        
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        response = await client.get(url, params=params)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            foods = data.get("foods", [])
            
            print(f"✅ API 连接成功！找到 {len(foods)} 个食物")
            print("\n搜索结果（苹果）：")
            
            for food in foods[:3]:
                name = food.get("description", "未知")
                fdc_id = food.get("fdcId", 0)
                category = food.get("foodCategory", "")
                print(f"  - {name} (ID: {fdc_id}) | {category}")
            
            # 试获取详细营养
            if foods:
                fdc_id = foods[0]["fdcId"]
                detail_url = f"https://api.nal.usda.gov/fdc/v1/foods/{fdc_id}"
                detail_resp = await client.get(detail_url, params={"api_key": api_key})
                
                if detail_resp.status_code == 200:
                    detail = detail_resp.json()
                    nutrients = detail.get("foodNutrients", [])
                    
                    # 关键营养素
                    key_codes = ["1008", "1003", "1004", "1089", "1095"]
                    
                    print(f"\n✅ 获取营养详情成功！")
                    print(f"\n苹果关键营养素（每100g）：")
                    
                    for n in nutrients:
                        code = str(n.get("nutrientNumber", ""))
                        if code in key_codes:
                            name = n.get("nutrientName", "")
                            value = n.get("value", 0)
                            unit = n.get("unitName", "")
                            print(f"  - {name}: {value} {unit}")
        else:
            print(f"❌ API 连接失败: {response.text}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_usda_api())