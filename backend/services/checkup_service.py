"""
产检模块业务逻辑服务
提供产检计划管理、结果录入、时间线等功能
"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import async_session_maker
from ..db.models import (
    CheckupPlan, CheckupResult, FamilyArchive,
    ReminderTask, ReminderType
)


class CheckupService:
    """产检业务服务"""
    
    # 标准产检计划模板（按孕周）
    CHECKUP_TEMPLATES = [
        {"week": 6, "type": "routine", "name": "早孕检查", "items": ["B超确认妊娠", "血常规", "尿常规"]},
        {"week": 8, "type": "routine", "name": "初次产检", "items": ["建档检查", "血常规", "尿常规", "肝肾功能", "心电图"]},
        {"week": 12, "type": "routine", "name": "常规产检", "items": ["NT检查", "血常规", "尿常规"]},
        {"week": 16, "type": "routine", "name": "常规产检", "items": ["血常规", "尿常规", "听胎心"]},
        {"week": 20, "type": "big_4d", "name": "大排畸", "items": ["四维彩超", "血常规", "尿常规"]},
        {"week": 24, "type": "glucose", "name": "糖耐量检查", "items": ["糖耐量试验", "血常规", "尿常规"], "notes": "需要空腹"},
        {"week": 28, "type": "routine", "name": "常规产检", "items": ["血常规", "尿常规", "听胎心", "测量宫高腹围"]},
        {"week": 30, "type": "routine", "name": "常规产检", "items": ["血常规", "尿常规", "B超"]},
        {"week": 32, "type": "routine", "name": "常规产检", "items": ["血常规", "尿常规", "胎心监护"]},
        {"week": 34, "type": "routine", "name": "常规产检", "items": ["血常规", "尿常规", "胎心监护", "B超"]},
        {"week": 36, "type": "routine", "name": "产前检查", "items": ["血常规", "尿常规", "胎心监护", "骨盆测量"]},
        {"week": 37, "type": "routine", "name": "产前检查", "items": ["血常规", "尿常规", "胎心监护", "B超", "评估分娩方式"]},
        {"week": 38, "type": "routine", "name": "产前检查", "items": ["血常规", "尿常规", "胎心监护"]},
        {"week": 39, "type": "routine", "name": "产前检查", "items": ["血常规", "尿常规", "胎心监护", "B超"]},
        {"week": 40, "type": "routine", "name": "产前检查", "items": ["血常规", "尿常规", "胎心监护", "评估分娩"]},
    ]

    async def create_plan(
        self,
        db: AsyncSession,
        archive_id: int,
        checkup_type: str,
        checkup_name: str,
        planned_date: date,
        hospital: Optional[str] = None,
        doctor: Optional[str] = None,
        department: Optional[str] = None,
        items: Optional[List[Dict]] = None,
        preparation_notes: Optional[str] = None,
        planned_time: Optional[time] = None,
        week_start: int = 0,
        week_end: int = 0
    ) -> CheckupPlan:
        """
        创建产检计划
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
            checkup_type: 产检类型
            checkup_name: 产检名称
            planned_date: 计划日期
            hospital: 医院
            doctor: 医生
            department: 科室
            items: 检查项目
            preparation_notes: 准备事项
            planned_time: 计划时间
            week_start: 孕周起始
            week_end: 孕周结束
        
        Returns:
            CheckupPlan: 创建的计划
        """
        plan = CheckupPlan(
            archive_id=archive_id,
            checkup_type=checkup_type,
            checkup_name=checkup_name,
            planned_date=planned_date,
            planned_time=planned_time,
            hospital=hospital,
            doctor=doctor,
            department=department,
            items=items,
            preparation_notes=preparation_notes,
            week_start=week_start,
            week_end=week_end,
            status="planned"
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        return plan

    async def generate_standard_plans(
        self,
        db: AsyncSession,
        archive_id: int,
        due_date: date,
        hospital: Optional[str] = None
    ) -> List[CheckupPlan]:
        """
        根据预产期生成标准产检计划
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
            due_date: 预产期
            hospital: 默认医院
        
        Returns:
            List[CheckupPlan]: 生成的计划列表
        """
        plans = []
        
        for template in self.CHECKUP_TEMPLATES:
            # 计算产检日期（从预产期倒推孕周）
            planned_date = due_date - timedelta(weeks=40 - template["week"])
            
            # 如果日期已过，跳过
            if planned_date < date.today() - timedelta(days=30):
                continue
            
            plan = await self.create_plan(
                db=db,
                archive_id=archive_id,
                checkup_type=template["type"],
                checkup_name=template["name"],
                planned_date=planned_date,
                hospital=hospital,
                items=[{"name": item} for item in template.get("items", [])],
                preparation_notes=template.get("notes"),
                week_start=template["week"],
                week_end=template["week"]
            )
            
            plans.append(plan)
        
        return plans

    async def get_plans(
        self,
        db: AsyncSession,
        archive_id: int,
        status: Optional[str] = None,
        upcoming_only: bool = False
    ) -> List[CheckupPlan]:
        """
        获取产检计划列表
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
            status: 状态筛选
            upcoming_only: 只显示即将到来的
        
        Returns:
            List[CheckupPlan]: 计划列表
        """
        conditions = [CheckupPlan.archive_id == archive_id]
        
        if status:
            conditions.append(CheckupPlan.status == status)
        
        if upcoming_only:
            conditions.append(CheckupPlan.planned_date >= date.today())
            conditions.append(CheckupPlan.status == "planned")
        
        stmt = select(CheckupPlan).where(and_(*conditions)).order_by(CheckupPlan.planned_date)
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_plan_status(
        self,
        db: AsyncSession,
        plan_id: int,
        status: str
    ) -> Optional[CheckupPlan]:
        """
        更新计划状态
        
        Args:
            db: 数据库会话
            plan_id: 计划ID
            status: 新状态
        
        Returns:
            Optional[CheckupPlan]: 更新后的计划
        """
        stmt = select(CheckupPlan).where(CheckupPlan.id == plan_id)
        result = await db.execute(stmt)
        plan = result.scalar_one_or_none()
        
        if plan:
            plan.status = status
            plan.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(plan)
        
        return plan

    async def add_result(
        self,
        db: AsyncSession,
        plan_id: int,
        archive_id: int,
        actual_date: date,
        result_data: Optional[List[Dict]] = None,
        doctor_notes: Optional[str] = None,
        suggestions: Optional[str] = None,
        attachment_urls: Optional[List[str]] = None
    ) -> CheckupResult:
        """
        添加产检结果
        
        Args:
            db: 数据库会话
            plan_id: 计划ID
            archive_id: 档案ID
            actual_date: 实际检查日期
            result_data: 结果数据
            doctor_notes: 医生意见
            suggestions: 建议
            attachment_urls: 附件URL
        
        Returns:
            CheckupResult: 创建的结果
        """
        # 检查是否有异常
        is_abnormal = False
        abnormal_items = []
        
        if result_data:
            for item in result_data:
                if item.get("is_abnormal"):
                    is_abnormal = True
                    abnormal_items.append(item.get("name", "未知项目"))
        
        result = CheckupResult(
            plan_id=plan_id,
            archive_id=archive_id,
            actual_date=actual_date,
            result_data=result_data,
            is_abnormal=is_abnormal,
            abnormal_items=", ".join(abnormal_items) if abnormal_items else None,
            doctor_notes=doctor_notes,
            suggestions=suggestions,
            attachment_urls=attachment_urls
        )
        
        db.add(result)
        
        # 更新计划状态为已完成
        await self.update_plan_status(db, plan_id, "completed")
        
        await db.commit()
        await db.refresh(result)
        
        return result

    async def get_results(
        self,
        db: AsyncSession,
        archive_id: int,
        plan_id: Optional[int] = None
    ) -> List[CheckupResult]:
        """
        获取产检结果
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
            plan_id: 计划ID（可选）
        
        Returns:
            List[CheckupResult]: 结果列表
        """
        conditions = [CheckupResult.archive_id == archive_id]
        
        if plan_id:
            conditions.append(CheckupResult.plan_id == plan_id)
        
        stmt = select(CheckupResult).where(and_(*conditions)).order_by(CheckupResult.actual_date.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_timeline(
        self,
        db: AsyncSession,
        archive_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取产检时间线
        
        整合计划和结果，展示完整时间线
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
        
        Returns:
            List[Dict]: 时间线事件列表
        """
        # 获取所有计划
        plans = await self.get_plans(db, archive_id)
        
        # 获取所有结果
        results = await self.get_results(db, archive_id)
        
        # 构建时间线
        timeline = []
        
        for plan in plans:
            event = {
                "id": plan.id,
                "type": "plan",
                "checkup_type": plan.checkup_type,
                "checkup_name": plan.checkup_name,
                "planned_date": plan.planned_date.isoformat(),
                "planned_time": plan.planned_time.isoformat() if plan.planned_time else None,
                "hospital": plan.hospital,
                "doctor": plan.doctor,
                "department": plan.department,
                "items": plan.items,
                "preparation_notes": plan.preparation_notes,
                "week_range": f"{plan.week_start}-{plan.week_end}周",
                "status": plan.status
            }
            
            # 如果有结果，补充结果信息
            plan_results = [r for r in results if r.plan_id == plan.id]
            if plan_results:
                latest_result = plan_results[0]
                event["has_result"] = True
                event["actual_date"] = latest_result.actual_date.isoformat()
                event["is_abnormal"] = latest_result.is_abnormal
                event["abnormal_items"] = latest_result.abnormal_items
                event["doctor_notes"] = latest_result.doctor_notes
                event["suggestions"] = latest_result.suggestions
            else:
                event["has_result"] = False
            
            timeline.append(event)
        
        # 按日期排序
        timeline.sort(key=lambda x: x["planned_date"], reverse=True)
        
        return timeline

    async def get_upcoming_checkups(
        self,
        db: AsyncSession,
        archive_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取即将到来的产检
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
            days: 未来多少天
        
        Returns:
            List[Dict]: 即将到来的产检列表
        """
        end_date = date.today() + timedelta(days=days)
        
        stmt = select(CheckupPlan).where(
            and_(
                CheckupPlan.archive_id == archive_id,
                CheckupPlan.planned_date >= date.today(),
                CheckupPlan.planned_date <= end_date,
                CheckupPlan.status == "planned"
            )
        ).order_by(CheckupPlan.planned_date)
        
        result = await db.execute(stmt)
        plans = result.scalars().all()
        
        upcoming = []
        for plan in plans:
            days_until = (plan.planned_date - date.today()).days
            upcoming.append({
                "id": plan.id,
                "name": plan.checkup_name,
                "date": plan.planned_date.isoformat(),
                "days_until": days_until,
                "hospital": plan.hospital,
                "items": plan.items,
                "preparation_notes": plan.preparation_notes,
                "urgency": "high" if days_until <= 3 else "normal" if days_until <= 7 else "low"
            })
        
        return upcoming

    async def get_checkup_stats(
        self,
        db: AsyncSession,
        archive_id: int
    ) -> Dict[str, Any]:
        """
        获取产检统计
        
        Args:
            db: 数据库会话
            archive_id: 档案ID
        
        Returns:
            Dict: 统计数据
        """
        # 计划统计
        total_plans = await db.execute(
            select(func.count()).select_from(CheckupPlan).where(CheckupPlan.archive_id == archive_id)
        )
        total = total_plans.scalar()
        
        completed_plans = await db.execute(
            select(func.count()).select_from(CheckupPlan).where(
                and_(CheckupPlan.archive_id == archive_id, CheckupPlan.status == "completed")
            )
        )
        completed = completed_plans.scalar()
        
        upcoming_plans = await db.execute(
            select(func.count()).select_from(CheckupPlan).where(
                and_(
                    CheckupPlan.archive_id == archive_id,
                    CheckupPlan.planned_date >= date.today(),
                    CheckupPlan.status == "planned"
                )
            )
        )
        upcoming = upcoming_plans.scalar()
        
        # 异常结果统计
        abnormal_results = await db.execute(
            select(func.count()).select_from(CheckupResult).where(
                and_(CheckupResult.archive_id == archive_id, CheckupResult.is_abnormal == True)
            )
        )
        abnormal_count = abnormal_results.scalar()
        
        return {
            "total_plans": total,
            "completed_plans": completed,
            "upcoming_plans": upcoming,
            "abnormal_results": abnormal_count,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0
        }


# 全局服务实例
_checkup_service: Optional[CheckupService] = None


def get_checkup_service() -> CheckupService:
    """获取产检服务实例"""
    global _checkup_service
    if _checkup_service is None:
        _checkup_service = CheckupService()
    return _checkup_service