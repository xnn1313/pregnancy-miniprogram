"""
每日记录 API 路由
对接 record_service 实现完整功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from ..db.database import get_db
from ..services.record_service import get_record_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/record", tags=["记录"])


# ==================== 请求模型 ====================

class RecordCreateRequest(BaseModel):
    """创建/更新记录请求"""
    member_id: int = Field(..., description="成员ID")
    archive_id: int = Field(..., description="档案ID")
    record_date: Optional[str] = Field(None, description="记录日期 YYYY-MM-DD，默认今天")
    
    # 体重
    weight: Optional[float] = Field(None, ge=30, le=200, description="体重(kg)")
    weight_change: Optional[float] = Field(None, description="体重变化(kg)")
    
    # 症状
    symptom_type: Optional[str] = Field(None, description="症状类型")
    symptom_severity: Optional[str] = Field(None, description="严重程度: none/mild/moderate/severe")
    symptom_notes: Optional[str] = Field(None, description="症状备注")
    
    # 情绪
    mood_level: Optional[str] = Field(None, description="情绪等级: great/good/normal/bad/terrible")
    mood_notes: Optional[str] = Field(None, description="情绪备注")
    
    # 饮食
    diet_summary: Optional[str] = Field(None, description="饮食摘要")
    diet_photo_urls: Optional[list] = Field(None, description="饮食照片URL列表")
    
    # 其他
    notes: Optional[str] = Field(None, description="其他备注")


class RecordQueryRequest(BaseModel):
    """查询记录请求"""
    member_id: int = Field(..., description="成员ID")
    page: Optional[int] = Field(1, ge=1, description="页码")
    page_size: Optional[int] = Field(10, ge=1, le=100, description="每页数量")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


# ==================== API 接口 ====================

@router.post("/")
async def save_record(
    request: RecordCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建或更新每日记录
    
    如果当天已有记录则更新，否则创建新记录
    """
    service = get_record_service()
    
    # 解析日期
    record_date = date.today()
    if request.record_date:
        try:
            record_date = date.fromisoformat(request.record_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    # 构建 kwargs
    kwargs = {}
    if request.weight is not None:
        kwargs["weight"] = request.weight
    if request.weight_change is not None:
        kwargs["weight_change"] = request.weight_change
    if request.symptom_type:
        kwargs["symptom_type"] = request.symptom_type
    if request.symptom_severity:
        from ..db.models import SymptomSeverity
        try:
            kwargs["symptom_severity"] = SymptomSeverity(request.symptom_severity)
        except ValueError:
            raise HTTPException(status_code=400, detail="症状严重程度值无效")
    if request.symptom_notes:
        kwargs["symptom_notes"] = request.symptom_notes
    if request.mood_level:
        from ..db.models import MoodLevel
        try:
            kwargs["mood_level"] = MoodLevel(request.mood_level)
        except ValueError:
            raise HTTPException(status_code=400, detail="情绪等级值无效")
    if request.mood_notes:
        kwargs["mood_notes"] = request.mood_notes
    if request.diet_summary:
        kwargs["diet_summary"] = request.diet_summary
    if request.diet_photo_urls:
        kwargs["diet_photo_urls"] = request.diet_photo_urls
    if request.notes:
        kwargs["notes"] = request.notes
    
    try:
        record = await service.create_or_update_record(
            db=db,
            member_id=request.member_id,
            archive_id=request.archive_id,
            record_date=record_date,
            **kwargs
        )
        
        return {
            "success": True,
            "record_id": record.id,
            "record_date": record.record_date.isoformat(),
            "message": "记录保存成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存记录失败: {str(e)}")


@router.get("/today")
async def get_today(
    member_id: int = Query(..., description="成员ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日记录
    
    返回今日的体重、症状、情绪等记录
    """
    service = get_record_service()
    
    try:
        record = await service.get_today_record(db, member_id)
        
        if not record:
            return {
                "has_record": False,
                "message": "今日暂无记录"
            }
        
        return {
            "has_record": True,
            "record_id": record.id,
            "record_date": record.record_date.isoformat(),
            "weight": record.weight,
            "weight_change": record.weight_change,
            "symptom_type": record.symptom_type,
            "symptom_severity": record.symptom_severity.value if record.symptom_severity else None,
            "symptom_notes": record.symptom_notes,
            "mood_level": record.mood_level.value if record.mood_level else None,
            "mood_notes": record.mood_notes,
            "diet_summary": record.diet_summary,
            "notes": record.notes,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")


@router.get("/history")
async def get_history(
    member_id: int = Query(..., description="成员ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取历史记录（分页）
    
    支持日期范围筛选
    """
    service = get_record_service()
    
    # 解析日期
    start = None
    end = None
    if start_date:
        try:
            start = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误")
    if end_date:
        try:
            end = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误")
    
    try:
        result = await service.get_record_history(
            db=db,
            member_id=member_id,
            page=page,
            page_size=page_size,
            start_date=start,
            end_date=end
        )
        
        # 格式化记录
        records = []
        for r in result["records"]:
            records.append({
                "id": r.id,
                "record_date": r.record_date.isoformat(),
                "weight": r.weight,
                "weight_change": r.weight_change,
                "symptom_type": r.symptom_type,
                "symptom_severity": r.symptom_severity.value if r.symptom_severity else None,
                "mood_level": r.mood_level.value if r.mood_level else None,
                "notes": r.notes
            })
        
        return {
            "records": records,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/weight/trend")
async def get_weight_trend(
    member_id: int = Query(..., description="成员ID"),
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取体重趋势
    
    返回体重变化曲线和建议
    """
    service = get_record_service()
    
    try:
        result = await service.get_weight_trend(db, member_id, days)
        
        return {
            "trend": result["trend"],
            "stats": result["stats"],
            "recommendation": result["recommendation"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取体重趋势失败: {str(e)}")


@router.get("/symptom/stats")
async def get_symptom_stats(
    member_id: int = Query(..., description="成员ID"),
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取症状统计
    
    返回症状类型分布和频率
    """
    service = get_record_service()
    
    try:
        result = await service.get_symptom_stats(db, member_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取症状统计失败: {str(e)}")


@router.get("/mood/analysis")
async def get_mood_analysis(
    member_id: int = Query(..., description="成员ID"),
    days: int = Query(30, ge=7, le=365, description="查询天数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取情绪分析
    
    返回情绪分布、趋势和建议
    """
    service = get_record_service()
    
    try:
        result = await service.get_mood_analysis(db, member_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取情绪分析失败: {str(e)}")


@router.get("/stats/overview")
async def get_stats_overview(
    member_id: int = Query(..., description="成员ID"),
    days: int = Query(30, ge=7, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取综合统计概览
    
    包含记录统计、体重趋势、症状统计、情绪分析
    """
    service = get_record_service()
    
    try:
        result = await service.get_combined_stats(db, member_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计概览失败: {str(e)}")