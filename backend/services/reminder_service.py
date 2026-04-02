"""
提醒模块业务逻辑服务
提供提醒任务管理、触达记录等功能
"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import async_session_maker
from ..db.models import (
    ReminderTask, ReminderDelivery, FamilyMember,
    ReminderType, ReminderChannel, DeliveryStatus
)


class ReminderService:
    """提醒业务服务"""
    
    # 提醒配额限制
    DAILY_QUOTA = {
        "wechat": 3,   # 微信订阅消息每天最多3条
        "in_app": 10   # 站内提醒每天最多10条
    }
    
    # 重试策略
    MAX_RETRIES = 3
    RETRY_INTERVALS = [5, 15, 60]  # 分钟

    async def create_task(
        self,
        db: AsyncSession,
        owner_id: int,
        archive_id: int,
        title: str,
        content: Optional[str] = None,
        reminder_type: str = "custom",
        trigger_date: date = None,
        trigger_time: time = None,
        channels: List[str] = ["in_app"],
        advance_minutes: int = 0,
        is_recurring: bool = False,
        recurring_pattern: Optional[str] = None,
        recurring_end_date: Optional[date] = None,
        checkup_id: Optional[int] = None
    ) -> ReminderTask:
        """
        创建提醒任务
        
        Args:
            db: 数据库会话
            owner_id: 接收者ID
            archive_id: 档案ID
            title: 提醒标题
            content: 提醒内容
            reminder_type: 提醒类型
            trigger_date: 触发日期
            trigger_time: 触发时间
            channels: 提醒渠道列表
            advance_minutes: 提前提醒分钟
            is_recurring: 是否重复
            recurring_pattern: 重复模式
            recurring_end_date: 重复结束日期
            checkup_id: 关联产检ID
        
        Returns:
            ReminderTask: 创建的任务
        """
        # 解析提醒类型
        try:
            r_type = ReminderType(reminder_type)
        except ValueError:
            r_type = ReminderType.CUSTOM
        
        task = ReminderTask(
            owner_id=owner_id,
            archive_id=archive_id,
            checkup_id=checkup_id,
            title=title,
            content=content,
            reminder_type=r_type,
            trigger_date=trigger_date,
            trigger_time=trigger_time,
            channels=",".join(channels),
            advance_minutes=advance_minutes,
            is_recurring=is_recurring,
            recurring_pattern=recurring_pattern,
            recurring_end_date=recurring_end_date,
            is_active=True
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return task

    async def get_tasks(
        self,
        db: AsyncSession,
        owner_id: int,
        active_only: bool = True,
        upcoming_only: bool = False
    ) -> List[ReminderTask]:
        """
        获取提醒任务列表
        
        Args:
            db: 数据库会话
            owner_id: 用户ID
            active_only: 只显示启用的
            upcoming_only: 只显示即将触发的
        
        Returns:
            List[ReminderTask]: 任务列表
        """
        conditions = [ReminderTask.owner_id == owner_id]
        
        if active_only:
            conditions.append(ReminderTask.is_active == True)
        
        if upcoming_only:
            conditions.append(ReminderTask.trigger_date >= date.today())
        
        stmt = select(ReminderTask).where(and_(*conditions)).order_by(
            ReminderTask.trigger_date,
            ReminderTask.trigger_time
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update_task(
        self,
        db: AsyncSession,
        task_id: int,
        **kwargs
    ) -> Optional[ReminderTask]:
        """
        更新提醒任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            **kwargs: 更新字段
        
        Returns:
            Optional[ReminderTask]: 更新后的任务
        """
        stmt = select(ReminderTask).where(ReminderTask.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        
        if task:
            for key, value in kwargs.items():
                if value is not None and hasattr(task, key):
                    setattr(task, key, value)
            
            task.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(task)
        
        return task

    async def delete_task(
        self,
        db: AsyncSession,
        task_id: int
    ) -> bool:
        """
        删除提醒任务（软删除，设置 is_active=False）
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        
        Returns:
            bool: 是否成功
        """
        stmt = select(ReminderTask).where(ReminderTask.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        
        if task:
            task.is_active = False
            task.updated_at = datetime.utcnow()
            await db.commit()
            return True
        
        return False

    async def create_delivery(
        self,
        db: AsyncSession,
        task_id: int,
        channel: str,
        scheduled_at: datetime
    ) -> ReminderDelivery:
        """
        创建触达记录
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            channel: 渠道
            scheduled_at: 计划发送时间
        
        Returns:
            ReminderDelivery: 创建的记录
        """
        try:
            r_channel = ReminderChannel(channel)
        except ValueError:
            r_channel = ReminderChannel.IN_APP
        
        delivery = ReminderDelivery(
            task_id=task_id,
            channel=r_channel,
            scheduled_at=scheduled_at,
            status=DeliveryStatus.PENDING
        )
        
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        
        return delivery

    async def get_pending_deliveries(
        self,
        db: AsyncSession,
        before_time: datetime = None
    ) -> List[ReminderDelivery]:
        """
        获取待发送的触达记录
        
        Args:
            db: 数据库会话
            before_time: 截止时间
        
        Returns:
            List[ReminderDelivery]: 待发送列表
        """
        conditions = [ReminderDelivery.status == DeliveryStatus.PENDING]
        
        if before_time:
            conditions.append(ReminderDelivery.scheduled_at <= before_time)
        
        stmt = select(ReminderDelivery).where(and_(*conditions)).order_by(
            ReminderDelivery.scheduled_at
        ).limit(100)
        
        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_delivery_sent(
        self,
        db: AsyncSession,
        delivery_id: int,
        external_id: Optional[str] = None
    ) -> Optional[ReminderDelivery]:
        """
        标记触达为已发送
        
        Args:
            db: 数据库会话
            delivery_id: 记录ID
            external_id: 外部消息ID
        
        Returns:
            Optional[ReminderDelivery]: 更新后的记录
        """
        stmt = select(ReminderDelivery).where(ReminderDelivery.id == delivery_id)
        result = await db.execute(stmt)
        delivery = result.scalar_one_or_none()
        
        if delivery:
            delivery.status = DeliveryStatus.SENT
            delivery.sent_at = datetime.utcnow()
            delivery.external_id = external_id
            await db.commit()
            await db.refresh(delivery)
        
        return delivery

    async def mark_delivery_failed(
        self,
        db: AsyncSession,
        delivery_id: int,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[ReminderDelivery]:
        """
        标记触达为失败
        
        Args:
            db: 数据库会话
            delivery_id: 记录ID
            error_code: 错误码
            error_message: 错误信息
        
        Returns:
            Optional[ReminderDelivery]: 更新后的记录
        """
        stmt = select(ReminderDelivery).where(ReminderDelivery.id == delivery_id)
        result = await db.execute(stmt)
        delivery = result.scalar_one_or_none()
        
        if delivery:
            delivery.status = DeliveryStatus.FAILED
            delivery.error_code = error_code
            delivery.error_message = error_message
            delivery.retry_count += 1
            
            # 计算下次重试时间
            if delivery.retry_count < self.MAX_RETRIES:
                retry_idx = min(delivery.retry_count - 1, len(self.RETRY_INTERVALS) - 1)
                delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=self.RETRY_INTERVALS[retry_idx])
                delivery.status = DeliveryStatus.PENDING  # 重置为待发送
            
            await db.commit()
            await db.refresh(delivery)
        
        return delivery

    async def check_daily_quota(
        self,
        db: AsyncSession,
        owner_id: int,
        channel: str
    ) -> Dict[str, Any]:
        """
        检查当日配额
        
        Args:
            db: 数据库会话
            owner_id: 用户ID
            channel: 渠道
        
        Returns:
            Dict: 配额信息
        """
        today = date.today()
        today_start = datetime.combine(today, time.min)
        today_end = datetime.combine(today, time.max)
        
        # 查询今日已发送数量
        count_stmt = select(func.count()).select_from(ReminderDelivery).where(
            and_(
                ReminderDelivery.task_id.in_(
                    select(ReminderTask.id).where(ReminderTask.owner_id == owner_id)
                ),
                ReminderDelivery.channel == ReminderChannel(channel),
                ReminderDelivery.sent_at >= today_start,
                ReminderDelivery.sent_at <= today_end,
                ReminderDelivery.status == DeliveryStatus.SENT
            )
        )
        
        result = await db.execute(count_stmt)
        sent_count = result.scalar()
        
        quota = self.DAILY_QUOTA.get(channel, 10)
        
        return {
            "channel": channel,
            "sent_count": sent_count,
            "quota": quota,
            "remaining": quota - sent_count,
            "is_available": sent_count < quota
        }

    async def generate_checkup_reminders(
        self,
        db: AsyncSession,
        checkup_id: int,
        owner_id: int,
        archive_id: int,
        planned_date: date,
        planned_time: Optional[time] = None,
        checkup_name: str = ""
    ) -> List[ReminderTask]:
        """
        为产检生成提醒任务
        
        默认生成提前1天和当天两条提醒
        
        Args:
            db: 数据库会话
            checkup_id: 产检ID
            owner_id: 用户ID
            archive_id: 档案ID
            planned_date: 产检日期
            planned_time: 产检时间
            checkup_name: 产检名称
        
        Returns:
            List[ReminderTask]: 生成的提醒任务
        """
        tasks = []
        
        # 提前1天提醒
        day_before = planned_date - timedelta(days=1)
        task1 = await self.create_task(
            db=db,
            owner_id=owner_id,
            archive_id=archive_id,
            title=f"产检提醒：{checkup_name}",
            content=f"明天({planned_date.strftime('%m月%d日')})有产检安排，请做好准备。",
            reminder_type="checkup",
            trigger_date=day_before,
            trigger_time=time(20, 0),  # 晚上8点提醒
            channels=["in_app"],
            checkup_id=checkup_id
        )
        tasks.append(task1)
        
        # 当天提醒
        trigger_time = planned_time if planned_time else time(8, 0)
        task2 = await self.create_task(
            db=db,
            owner_id=owner_id,
            archive_id=archive_id,
            title=f"产检提醒：{checkup_name}",
            content=f"今天({planned_date.strftime('%m月%d日')})有产检安排，请准时前往。",
            reminder_type="checkup",
            trigger_date=planned_date,
            trigger_time=trigger_time,
            channels=["in_app", "wechat"],
            advance_minutes=30,
            checkup_id=checkup_id
        )
        tasks.append(task2)
        
        return tasks

    async def get_reminder_stats(
        self,
        db: AsyncSession,
        owner_id: int
    ) -> Dict[str, Any]:
        """
        获取提醒统计
        
        Args:
            db: 数据库会话
            owner_id: 用户ID
        
        Returns:
            Dict: 统计数据
        """
        # 总任务数
        total_tasks = await db.execute(
            select(func.count()).select_from(ReminderTask).where(ReminderTask.owner_id == owner_id)
        )
        total = total_tasks.scalar()
        
        # 启用任务数
        active_tasks = await db.execute(
            select(func.count()).select_from(ReminderTask).where(
                and_(ReminderTask.owner_id == owner_id, ReminderTask.is_active == True)
            )
        )
        active = active_tasks.scalar()
        
        # 今日触发数
        today = date.today()
        today_deliveries = await db.execute(
            select(func.count()).select_from(ReminderDelivery).where(
                and_(
                    ReminderDelivery.task_id.in_(
                        select(ReminderTask.id).where(ReminderTask.owner_id == owner_id)
                    ),
                    ReminderDelivery.scheduled_at >= datetime.combine(today, time.min),
                    ReminderDelivery.scheduled_at <= datetime.combine(today, time.max)
                )
            )
        )
        today_count = today_deliveries.scalar()
        
        # 成功/失败数
        success_count = await db.execute(
            select(func.count()).select_from(ReminderDelivery).where(
                and_(
                    ReminderDelivery.task_id.in_(
                        select(ReminderTask.id).where(ReminderTask.owner_id == owner_id)
                    ),
                    ReminderDelivery.status == DeliveryStatus.SENT
                )
            )
        )
        success = success_count.scalar()
        
        failed_count = await db.execute(
            select(func.count()).select_from(ReminderDelivery).where(
                and_(
                    ReminderDelivery.task_id.in_(
                        select(ReminderTask.id).where(ReminderTask.owner_id == owner_id)
                    ),
                    ReminderDelivery.status == DeliveryStatus.FAILED
                )
            )
        )
        failed = failed_count.scalar()
        
        return {
            "total_tasks": total,
            "active_tasks": active,
            "today_deliveries": today_count,
            "success_count": success,
            "failed_count": failed,
            "success_rate": round(success / (success + failed) * 100, 1) if (success + failed) > 0 else 0
        }


# 全局服务实例
_reminder_service: Optional[ReminderService] = None


def get_reminder_service() -> ReminderService:
    """获取提醒服务实例"""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service