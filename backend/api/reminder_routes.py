"""
提醒 API 路由
对接 reminder_service 实现完整功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date, time, datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.reminder_service import get_reminder_service

router = APIRouter(prefix="/api/v1/reminder", tags=["提醒"])


# ==================== 请求模型 ====================

class ReminderTaskCreate(BaseModel):
    """创建提醒任务请求"""
    owner_id: int = Field(..., description="接收者ID")
    archive_id: int = Field(..., description="档案ID")
    title: str = Field(..., max_length=200, description="提醒标题")
    content: Optional[str] = Field(None, description="提醒内容")
    reminder_type: Optional[str] = Field("custom", description="提醒类型: checkup/medicine/nutrition/custom")
    trigger_date: str = Field(..., description="触发日期 YYYY-MM-DD")
    trigger_time: str = Field(..., description="触发时间 HH:MM")
    channels: Optional[List[str]] = Field(["in_app"], description="提醒渠道列表")
    advance_minutes: Optional[int] = Field(0, description="提前提醒分钟")
    is_recurring: Optional[bool] = Field(False, description="是否重复")
    recurring_pattern: Optional[str] = Field(None, description="重复模式: daily/weekly/monthly")
    recurring_end_date: Optional[str] = Field(None, description="重复结束日期")
    checkup_id: Optional[int] = Field(None, description="关联产检ID")


class ReminderTaskUpdate(BaseModel):
    """更新提醒任务请求"""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None)
    trigger_date: Optional[str] = Field(None)
    trigger_time: Optional[str] = Field(None)
    channels: Optional[List[str]] = Field(None)
    advance_minutes: Optional[int] = Field(None)
    is_recurring: Optional[bool] = Field(None)
    recurring_pattern: Optional[str] = Field(None)
    recurring_end_date: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class GenerateCheckupReminder(BaseModel):
    """为产检生成提醒请求"""
    checkup_id: int = Field(..., description="产检ID")
    owner_id: int = Field(..., description="接收者ID")
    archive_id: int = Field(..., description="档案ID")
    planned_date: str = Field(..., description="产检日期 YYYY-MM-DD")
    planned_time: Optional[str] = Field(None, description="产检时间 HH:MM")
    checkup_name: str = Field(..., description="产检名称")


# ==================== API 接口 ====================

@router.post("/task")
async def create_task(
    request: ReminderTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建提醒任务
    
    支持单次和重复提醒
    """
    service = get_reminder_service()
    
    # 解析日期时间
    try:
        trigger_date = date.fromisoformat(request.trigger_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    try:
        trigger_time = time.fromisoformat(request.trigger_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式错误，应为 HH:MM")
    
    # 解析重复结束日期
    recurring_end = None
    if request.recurring_end_date:
        try:
            recurring_end = date.fromisoformat(request.recurring_end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="重复结束日期格式错误")
    
    # 检查配额
    for channel in request.channels or ["in_app"]:
        quota_info = await service.check_daily_quota(db, request.owner_id, channel)
        if not quota_info["is_available"]:
            raise HTTPException(
                status_code=429,
                detail=f"{channel} 渠道今日配额已用完（{quota_info['quota']}条/天）"
            )
    
    try:
        task = await service.create_task(
            db=db,
            owner_id=request.owner_id,
            archive_id=request.archive_id,
            title=request.title,
            content=request.content,
            reminder_type=request.reminder_type or "custom",
            trigger_date=trigger_date,
            trigger_time=trigger_time,
            channels=request.channels or ["in_app"],
            advance_minutes=request.advance_minutes or 0,
            is_recurring=request.is_recurring or False,
            recurring_pattern=request.recurring_pattern,
            recurring_end_date=recurring_end,
            checkup_id=request.checkup_id
        )
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "提醒任务创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建提醒任务失败: {str(e)}")


@router.post("/generate-checkup")
async def generate_checkup_reminder(
    request: GenerateCheckupReminder,
    db: AsyncSession = Depends(get_db)
):
    """
    为产检自动生成提醒
    
    生成提前1天和当天两条提醒
    """
    service = get_reminder_service()
    
    try:
        planned_date = date.fromisoformat(request.planned_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    planned_time = None
    if request.planned_time:
        try:
            planned_time = time.fromisoformat(request.planned_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式错误")
    
    try:
        tasks = await service.generate_checkup_reminders(
            db=db,
            checkup_id=request.checkup_id,
            owner_id=request.owner_id,
            archive_id=request.archive_id,
            planned_date=planned_date,
            planned_time=planned_time,
            checkup_name=request.checkup_name
        )
        
        return {
            "success": True,
            "generated_count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "trigger_date": t.trigger_date.isoformat(),
                    "trigger_time": t.trigger_time.isoformat()
                }
                for t in tasks
            ],
            "message": f"已生成 {len(tasks)} 条产检提醒"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成产检提醒失败: {str(e)}")


@router.get("/tasks")
async def list_tasks(
    owner_id: int = Query(..., description="用户ID"),
    active_only: bool = Query(True, description="只显示启用的"),
    upcoming_only: bool = Query(False, description="只显示即将触发的"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取提醒任务列表
    """
    service = get_reminder_service()
    
    try:
        tasks = await service.get_tasks(
            db=db,
            owner_id=owner_id,
            active_only=active_only,
            upcoming_only=upcoming_only
        )
        
        return {
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "content": t.content,
                    "reminder_type": t.reminder_type.value,
                    "trigger_date": t.trigger_date.isoformat(),
                    "trigger_time": t.trigger_time.isoformat(),
                    "channels": t.channels.split(","),
                    "advance_minutes": t.advance_minutes,
                    "is_recurring": t.is_recurring,
                    "recurring_pattern": t.recurring_pattern,
                    "is_active": t.is_active,
                    "checkup_id": t.checkup_id,
                    "last_triggered_at": t.last_triggered_at.isoformat() if t.last_triggered_at else None,
                    "days_until": (t.trigger_date - date.today()).days if t.is_active and t.trigger_date >= date.today() else None
                }
                for t in tasks
            ],
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提醒任务失败: {str(e)}")


@router.put("/task/{task_id}")
async def update_task(
    task_id: int,
    request: ReminderTaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新提醒任务
    """
    service = get_reminder_service()
    
    # 解析日期时间
    kwargs = {}
    
    if request.title:
        kwargs["title"] = request.title
    if request.content:
        kwargs["content"] = request.content
    if request.trigger_date:
        try:
            kwargs["trigger_date"] = date.fromisoformat(request.trigger_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误")
    if request.trigger_time:
        try:
            kwargs["trigger_time"] = time.fromisoformat(request.trigger_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="时间格式错误")
    if request.channels:
        kwargs["channels"] = ",".join(request.channels)
    if request.advance_minutes is not None:
        kwargs["advance_minutes"] = request.advance_minutes
    if request.is_recurring is not None:
        kwargs["is_recurring"] = request.is_recurring
    if request.recurring_pattern:
        kwargs["recurring_pattern"] = request.recurring_pattern
    if request.recurring_end_date:
        try:
            kwargs["recurring_end_date"] = date.fromisoformat(request.recurring_end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="重复结束日期格式错误")
    if request.is_active is not None:
        kwargs["is_active"] = request.is_active
    
    try:
        task = await service.update_task(db, task_id, **kwargs)
        
        if not task:
            raise HTTPException(status_code=404, detail="提醒任务不存在")
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "提醒任务更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新提醒任务失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除提醒任务（软删除）
    """
    service = get_reminder_service()
    
    try:
        success = await service.delete_task(db, task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="提醒任务不存在")
        
        return {
            "success": True,
            "message": "提醒任务已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除提醒任务失败: {str(e)}")


@router.get("/quota")
async def check_quota(
    owner_id: int = Query(..., description="用户ID"),
    channel: str = Query("in_app", description="渠道: in_app/wechat"),
    db: AsyncSession = Depends(get_db)
):
    """
    检查当日提醒配额
    """
    service = get_reminder_service()
    
    try:
        quota_info = await service.check_daily_quota(db, owner_id, channel)
        return quota_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查配额失败: {str(e)}")


@router.get("/stats")
async def get_stats(
    owner_id: int = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取提醒统计
    """
    service = get_reminder_service()
    
    try:
        stats = await service.get_reminder_stats(db, owner_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")