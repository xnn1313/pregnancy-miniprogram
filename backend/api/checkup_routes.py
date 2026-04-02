"""
产检 API 路由
对接 checkup_service 实现完整功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.checkup_service import get_checkup_service

router = APIRouter(prefix="/api/v1/checkup", tags=["产检"])


# ==================== 请求模型 ====================

class CheckupPlanCreate(BaseModel):
    """创建产检计划请求"""
    archive_id: int = Field(..., description="档案ID")
    checkup_type: str = Field(..., description="产检类型: routine/nt/big_4d/glucose/blood/urine/other")
    checkup_name: str = Field(..., description="产检名称")
    planned_date: str = Field(..., description="计划日期 YYYY-MM-DD")
    planned_time: Optional[str] = Field(None, description="计划时间 HH:MM")
    hospital: Optional[str] = Field(None, description="医院")
    doctor: Optional[str] = Field(None, description="医生")
    department: Optional[str] = Field(None, description="科室")
    items: Optional[List[Dict]] = Field(None, description="检查项目列表")
    preparation_notes: Optional[str] = Field(None, description="准备事项")
    week_start: Optional[int] = Field(0, description="孕周起始")
    week_end: Optional[int] = Field(0, description="孕周结束")


class CheckupResultCreate(BaseModel):
    """添加产检结果请求"""
    plan_id: int = Field(..., description="计划ID")
    archive_id: int = Field(..., description="档案ID")
    actual_date: str = Field(..., description="实际检查日期 YYYY-MM-DD")
    result_data: Optional[List[Dict]] = Field(None, description="检查结果数据")
    doctor_notes: Optional[str] = Field(None, description="医生意见")
    suggestions: Optional[str] = Field(None, description="建议")
    attachment_urls: Optional[List[str]] = Field(None, description="附件URL列表")


class GenerateStandardPlans(BaseModel):
    """生成标准产检计划请求"""
    archive_id: int = Field(..., description="档案ID")
    due_date: str = Field(..., description="预产期 YYYY-MM-DD")
    hospital: Optional[str] = Field(None, description="默认医院")


# ==================== API 接口 ====================

@router.post("/plan")
async def create_plan(
    request: CheckupPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建单个产检计划
    """
    service = get_checkup_service()
    
    # 解析日期
    try:
        planned_date = date.fromisoformat(request.planned_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    # 解析时间
    planned_time = None
    if request.planned_time:
        try:
            planned_time = time.fromisoformat(request.planned_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式错误，应为 HH:MM")
    
    try:
        plan = await service.create_plan(
            db=db,
            archive_id=request.archive_id,
            checkup_type=request.checkup_type,
            checkup_name=request.checkup_name,
            planned_date=planned_date,
            planned_time=planned_time,
            hospital=request.hospital,
            doctor=request.doctor,
            department=request.department,
            items=request.items,
            preparation_notes=request.preparation_notes,
            week_start=request.week_start or 0,
            week_end=request.week_end or 0
        )
        
        return {
            "success": True,
            "plan_id": plan.id,
            "message": "产检计划创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建产检计划失败: {str(e)}")


@router.post("/generate-standard")
async def generate_standard_plans(
    request: GenerateStandardPlans,
    db: AsyncSession = Depends(get_db)
):
    """
    根据预产期自动生成标准产检计划
    
    生成从当前孕周到40周的完整产检计划
    """
    service = get_checkup_service()
    
    try:
        due_date = date.fromisoformat(request.due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="预产期格式错误，应为 YYYY-MM-DD")
    
    try:
        plans = await service.generate_standard_plans(
            db=db,
            archive_id=request.archive_id,
            due_date=due_date,
            hospital=request.hospital
        )
        
        return {
            "success": True,
            "generated_count": len(plans),
            "plans": [
                {
                    "id": p.id,
                    "name": p.checkup_name,
                    "date": p.planned_date.isoformat(),
                    "type": p.checkup_type,
                    "week": f"{p.week_start}周"
                }
                for p in plans
            ],
            "message": f"已生成 {len(plans)} 个产检计划"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成产检计划失败: {str(e)}")


@router.get("/plans")
async def list_plans(
    archive_id: int = Query(..., description="档案ID"),
    status: Optional[str] = Query(None, description="状态筛选: planned/completed/cancelled"),
    upcoming_only: bool = Query(False, description="只显示即将到来的"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取产检计划列表
    
    支持状态筛选和即将到来筛选
    """
    service = get_checkup_service()
    
    try:
        plans = await service.get_plans(
            db=db,
            archive_id=archive_id,
            status=status,
            upcoming_only=upcoming_only
        )
        
        return {
            "plans": [
                {
                    "id": p.id,
                    "name": p.checkup_name,
                    "type": p.checkup_type,
                    "planned_date": p.planned_date.isoformat(),
                    "planned_time": p.planned_time.isoformat() if p.planned_time else None,
                    "hospital": p.hospital,
                    "doctor": p.doctor,
                    "department": p.department,
                    "items": p.items,
                    "preparation_notes": p.preparation_notes,
                    "week_range": f"{p.week_start}-{p.week_end}周",
                    "status": p.status,
                    "days_until": (p.planned_date - date.today()).days if p.status == "planned" else None
                }
                for p in plans
            ],
            "total": len(plans)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取产检计划失败: {str(e)}")


@router.post("/result")
async def add_result(
    request: CheckupResultCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    添加产检结果
    
    同时会更新对应计划的状态为已完成
    """
    service = get_checkup_service()
    
    try:
        actual_date = date.fromisoformat(request.actual_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    try:
        result = await service.add_result(
            db=db,
            plan_id=request.plan_id,
            archive_id=request.archive_id,
            actual_date=actual_date,
            result_data=request.result_data,
            doctor_notes=request.doctor_notes,
            suggestions=request.suggestions,
            attachment_urls=request.attachment_urls
        )
        
        return {
            "success": True,
            "result_id": result.id,
            "is_abnormal": result.is_abnormal,
            "abnormal_items": result.abnormal_items,
            "message": "产检结果添加成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加产检结果失败: {str(e)}")


@router.get("/timeline")
async def get_timeline(
    archive_id: int = Query(..., description="档案ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取产检时间线
    
    整合计划和结果，展示完整产检历史
    """
    service = get_checkup_service()
    
    try:
        timeline = await service.get_timeline(db, archive_id)
        return {
            "timeline": timeline,
            "total": len(timeline)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取产检时间线失败: {str(e)}")


@router.get("/upcoming")
async def get_upcoming(
    archive_id: int = Query(..., description="档案ID"),
    days: int = Query(30, ge=1, le=365, description="未来多少天"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取即将到来的产检
    
    按紧急程度分类展示
    """
    service = get_checkup_service()
    
    try:
        upcoming = await service.get_upcoming_checkups(db, archive_id, days)
        return {
            "upcoming": upcoming,
            "total": len(upcoming),
            "high_priority": len([u for u in upcoming if u["urgency"] == "high"]),
            "normal_priority": len([u for u in upcoming if u["urgency"] == "normal"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取即将产检失败: {str(e)}")


@router.get("/stats")
async def get_stats(
    archive_id: int = Query(..., description="档案ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取产检统计
    
    包括完成率、异常结果数等
    """
    service = get_checkup_service()
    
    try:
        stats = await service.get_checkup_stats(db, archive_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取产检统计失败: {str(e)}")


@router.put("/plan/{plan_id}/status")
async def update_plan_status(
    plan_id: int,
    status: str = Query(..., description="新状态: planned/completed/cancelled/rescheduled"),
    db: AsyncSession = Depends(get_db)
):
    """
    更新产检计划状态
    """
    service = get_checkup_service()
    
    valid_statuses = ["planned", "completed", "cancelled", "rescheduled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，允许值: {valid_statuses}")
    
    try:
        plan = await service.update_plan_status(db, plan_id, status)
        
        if not plan:
            raise HTTPException(status_code=404, detail="产检计划不存在")
        
        return {
            "success": True,
            "plan_id": plan.id,
            "new_status": plan.status,
            "message": "状态更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")