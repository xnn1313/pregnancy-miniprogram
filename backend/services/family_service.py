"""
家庭档案业务逻辑服务
包含孕周计算、孕期阶段判断、成员权限校验等功能
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import async_session_maker
from ..db.models import FamilyArchive, FamilyMember, MemberRole


class PregnancyStage(str, Enum):
    """孕期阶段"""
    EARLY = "early"      # 早期：1-12周
    MIDDLE = "middle"    # 中期：13-27周
    LATE = "late"        # 晚期：28-40+周


class PermissionLevel(str, Enum):
    """权限级别"""
    OWNER = "owner"      # 孕妇本人：完全控制
    PARTNER = "partner"  # 配偶：可查看、可记录
    VIEWER = "viewer"    # 观察者：只读（预留）


# ==================== 孕周计算 ====================

def calculate_due_date(last_period_date: date) -> date:
    """
    根据末次月经日期计算预产期
    使用 Naegele 规则：末次月经第一天 + 280天
    
    Args:
        last_period_date: 末次月经第一天
        
    Returns:
        预产期日期
    """
    return last_period_date + timedelta(days=280)


def calculate_pregnancy_week(due_date: date, current_date: Optional[date] = None) -> Tuple[int, int]:
    """
    根据预产期计算当前孕周
    
    Args:
        due_date: 预产期
        current_date: 当前日期，默认为今天
        
    Returns:
        (孕周, 天数) 元组，如 (20, 3) 表示孕20周+3天
    """
    if current_date is None:
        current_date = date.today()
    
    # 从预产期倒推：预产期 = 孕40周
    # 所以孕周 = 40 - (预产期 - 当前日期) / 7
    days_to_due = (due_date - current_date).days
    
    if days_to_due >= 280:
        # 还没怀孕或刚怀孕
        return (0, 0)
    
    if days_to_due <= 0:
        # 已过预产期
        total_days = 280 + abs(days_to_due)
    else:
        total_days = 280 - days_to_due
    
    weeks = total_days // 7
    days = total_days % 7
    
    return (weeks, days)


def get_pregnancy_stage(weeks: int) -> PregnancyStage:
    """
    根据孕周判断孕期阶段
    
    Args:
        weeks: 孕周数
        
    Returns:
        孕期阶段枚举值
    """
    if weeks <= 12:
        return PregnancyStage.EARLY
    elif weeks <= 27:
        return PregnancyStage.MIDDLE
    else:
        return PregnancyStage.LATE


def get_trimester(weeks: int) -> int:
    """
    获取孕期三阶段数字表示（兼容数据库字段）
    
    Args:
        weeks: 孕周数
        
    Returns:
        1/2/3 分别代表早/中/晚期
    """
    stage = get_pregnancy_stage(weeks)
    if stage == PregnancyStage.EARLY:
        return 1
    elif stage == PregnancyStage.MIDDLE:
        return 2
    else:
        return 3


def get_stage_name(stage: int) -> str:
    """
    获取孕期阶段中文名称
    
    Args:
        stage: 阶段数字（1/2/3）
        
    Returns:
        阶段名称
    """
    names = {
        1: "孕早期",
        2: "孕中期",
        3: "孕晚期"
    }
    return names.get(stage, "未知")


# ==================== 孕期健康指标 ====================

def get_recommended_weight_gain(pre_pregnancy_weight: float, bmi: float, weeks: int) -> Dict[str, float]:
    """
    获取推荐体重增长范围
    
    Args:
        pre_pregnancy_weight: 孕前体重(kg)
        bmi: 孕前BMI
        weeks: 当前孕周
        
    Returns:
        推荐体重增长范围
    """
    # 根据BMI确定总体重增长范围
    if bmi < 18.5:  # 偏瘦
        total_gain = (12.5, 18.0)
        weekly_rate = 0.51
    elif bmi < 24.0:  # 正常
        total_gain = (11.5, 16.0)
        weekly_rate = 0.42
    elif bmi < 28.0:  # 超重
        total_gain = (7.0, 11.5)
        weekly_rate = 0.28
    else:  # 肥胖
        total_gain = (5.0, 9.0)
        weekly_rate = 0.22
    
    # 根据孕周调整
    if weeks <= 12:
        # 早期体重增长较少
        return {
            "recommended_gain": (0.5, 2.0),
            "total_range": total_gain,
            "weekly_rate": weekly_rate
        }
    else:
        # 中晚期按周增长
        early_gain = 2.0
        mid_late_weeks = weeks - 12
        expected_gain = early_gain + mid_late_weeks * weekly_rate
        
        return {
            "recommended_gain": (expected_gain - 2, expected_gain + 2),
            "total_range": total_gain,
            "weekly_rate": weekly_rate
        }


def calculate_bmi(weight: float, height: float) -> float:
    """
    计算BMI
    
    Args:
        weight: 体重(kg)
        height: 身高(cm)
        
    Returns:
        BMI值
    """
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


# ==================== 家庭邀请码 ====================

def generate_family_code() -> str:
    """
    生成家庭邀请码
    格式：6位大写字母+数字组合
    
    Returns:
        邀请码字符串
    """
    import random
    import string
    
    chars = string.ascii_uppercase + string.digits
    # 确保至少包含1个字母和1个数字
    code = [
        random.choice(string.ascii_uppercase),
        random.choice(string.digits)
    ]
    # 填充剩余4位
    code += [random.choice(chars) for _ in range(4)]
    random.shuffle(code)
    return ''.join(code)


# ==================== 成员权限校验 ====================

class PermissionChecker:
    """成员权限校验器"""
    
    @staticmethod
    async def get_member_by_openid(db: AsyncSession, openid: str) -> Optional[FamilyMember]:
        """通过 openid 获取成员"""
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.openid == openid)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_archive_by_id(db: AsyncSession, archive_id: int) -> Optional[FamilyArchive]:
        """通过 ID 获取档案"""
        result = await db.execute(
            select(FamilyArchive).where(FamilyArchive.id == archive_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_archive_by_code(db: AsyncSession, family_code: str) -> Optional[FamilyArchive]:
        """通过邀请码获取档案"""
        result = await db.execute(
            select(FamilyArchive).where(FamilyArchive.family_code == family_code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def check_member_permission(
        db: AsyncSession,
        openid: str,
        archive_id: int,
        required_level: PermissionLevel = PermissionLevel.PARTNER
    ) -> Tuple[bool, Optional[str], Optional[FamilyMember]]:
        """
        检查成员权限
        
        Args:
            db: 数据库会话
            openid: 用户 openid
            archive_id: 档案 ID
            required_level: 所需权限级别
            
        Returns:
            (是否有权限, 错误消息, 成员对象)
        """
        member = await PermissionChecker.get_member_by_openid(db, openid)
        
        if not member:
            return False, "用户不存在", None
        
        if member.archive_id != archive_id:
            return False, "无权访问此档案", None
        
        if not member.is_active:
            return False, "成员已禁用", None
        
        # 权限级别比较
        level_map = {
            MemberRole.OWNER: PermissionLevel.OWNER,
            MemberRole.PARTNER: PermissionLevel.PARTNER
        }
        
        member_level = level_map.get(member.role, PermissionLevel.VIEWER)
        
        # OWNER > PARTNER > VIEWER
        level_order = [PermissionLevel.VIEWER, PermissionLevel.PARTNER, PermissionLevel.OWNER]
        if level_order.index(member_level) < level_order.index(required_level):
            return False, f"权限不足，需要 {required_level} 级别", member
        
        return True, None, member
    
    @staticmethod
    async def is_owner(db: AsyncSession, openid: str, archive_id: int) -> bool:
        """检查是否是孕妇本人"""
        has_permission, _, member = await PermissionChecker.check_member_permission(
            db, openid, archive_id, PermissionLevel.OWNER
        )
        return has_permission and member is not None and member.role == MemberRole.OWNER
    
    @staticmethod
    async def can_edit(db: AsyncSession, openid: str, archive_id: int) -> bool:
        """检查是否有编辑权限"""
        has_permission, _, _ = await PermissionChecker.check_member_permission(
            db, openid, archive_id, PermissionLevel.PARTNER
        )
        return has_permission
    
    @staticmethod
    async def can_view(db: AsyncSession, openid: str, archive_id: int) -> bool:
        """检查是否有查看权限"""
        has_permission, _, _ = await PermissionChecker.check_member_permission(
            db, openid, archive_id, PermissionLevel.VIEWER
        )
        return has_permission


# ==================== 家庭服务 ====================

class FamilyService:
    """家庭档案服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_archive(
        self,
        openid: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        due_date: Optional[date] = None,
        last_period_date: Optional[date] = None,
        pre_pregnancy_weight: Optional[float] = None,
        height: Optional[float] = None,
        age: Optional[int] = None
    ) -> Tuple[FamilyArchive, FamilyMember]:
        """
        创建家庭档案
        
        Args:
            openid: 用户 openid
            nickname: 昵称
            avatar_url: 头像
            due_date: 预产期
            last_period_date: 末次月经日期
            pre_pregnancy_weight: 孕前体重
            height: 身高
            age: 年龄
            
        Returns:
            (档案对象, 成员对象)
        """
        # 生成唯一的家庭邀请码
        family_code = generate_family_code()
        while await PermissionChecker.get_archive_by_code(self.db, family_code):
            family_code = generate_family_code()
        
        # 计算孕周
        pregnancy_weeks = 0
        pregnancy_days = 0
        trimester = 1
        
        if due_date:
            pregnancy_weeks, pregnancy_days = calculate_pregnancy_week(due_date)
            trimester = get_trimester(pregnancy_weeks)
        
        # 创建档案
        archive = FamilyArchive(
            family_code=family_code,
            due_date=due_date,
            last_period_date=last_period_date,
            pregnancy_weeks=pregnancy_weeks,
            pregnancy_days=pregnancy_days,
            trimester=trimester,
            pre_pregnancy_weight=pre_pregnancy_weight,
            height=height,
            age=age,
            is_high_risk=False
        )
        self.db.add(archive)
        await self.db.flush()
        
        # 创建成员（孕妇本人）
        member = FamilyMember(
            archive_id=archive.id,
            openid=openid,
            nickname=nickname,
            avatar_url=avatar_url,
            role=MemberRole.OWNER,
            notification_enabled=True,
            is_active=True
        )
        self.db.add(member)
        await self.db.flush()
        
        return archive, member
    
    async def get_archive(self, archive_id: int) -> Optional[FamilyArchive]:
        """获取档案"""
        return await PermissionChecker.get_archive_by_id(self.db, archive_id)
    
    async def get_archive_by_openid(self, openid: str) -> Optional[FamilyArchive]:
        """通过 openid 获取用户所在档案"""
        member = await PermissionChecker.get_member_by_openid(self.db, openid)
        if member:
            return await self.get_archive(member.archive_id)
        return None
    
    async def update_archive(
        self,
        archive_id: int,
        **kwargs
    ) -> Optional[FamilyArchive]:
        """
        更新档案信息
        
        支持更新的字段：
        - due_date: 预产期
        - last_period_date: 末次月经日期
        - pre_pregnancy_weight: 孕前体重
        - height: 身高
        - age: 年龄
        - is_high_risk: 高危标记
        - high_risk_notes: 高危因素说明
        """
        archive = await self.get_archive(archive_id)
        if not archive:
            return None
        
        # 更新字段
        updatable_fields = [
            'due_date', 'last_period_date', 'pre_pregnancy_weight',
            'height', 'age', 'is_high_risk', 'high_risk_notes'
        ]
        
        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(archive, field, kwargs[field])
        
        # 如果更新了预产期，重新计算孕周
        if 'due_date' in kwargs and kwargs['due_date']:
            archive.pregnancy_weeks, archive.pregnancy_days = calculate_pregnancy_week(kwargs['due_date'])
            archive.trimester = get_trimester(archive.pregnancy_weeks)
        
        archive.updated_at = datetime.utcnow()
        await self.db.flush()
        
        return archive
    
    async def update_pregnancy_progress(self, archive_id: int) -> Optional[FamilyArchive]:
        """
        更新孕周进度（定时任务调用）
        
        根据当前日期重新计算孕周
        """
        archive = await self.get_archive(archive_id)
        if not archive or not archive.due_date:
            return None
        
        archive.pregnancy_weeks, archive.pregnancy_days = calculate_pregnancy_week(archive.due_date)
        archive.trimester = get_trimester(archive.pregnancy_weeks)
        archive.updated_at = datetime.utcnow()
        await self.db.flush()
        
        return archive
    
    async def invite_member(
        self,
        archive_id: int,
        openid: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        role: MemberRole = MemberRole.PARTNER,
        relation: Optional[str] = None
    ) -> Tuple[bool, Optional[FamilyMember], str]:
        """
        邀请成员加入家庭
        
        Args:
            archive_id: 档案 ID
            openid: 新成员 openid
            nickname: 昵称
            avatar_url: 头像
            role: 角色
            relation: 与孕妇关系
            
        Returns:
            (成功与否, 成员对象, 消息)
        """
        # 检查档案是否存在
        archive = await self.get_archive(archive_id)
        if not archive:
            return False, None, "档案不存在"
        
        # 检查用户是否已加入其他家庭
        existing_member = await PermissionChecker.get_member_by_openid(self.db, openid)
        if existing_member and existing_member.is_active:
            return False, None, "用户已加入其他家庭"
        
        # 如果用户存在但不活跃，重新激活
        if existing_member and not existing_member.is_active:
            existing_member.is_active = True
            existing_member.nickname = nickname or existing_member.nickname
            existing_member.avatar_url = avatar_url or existing_member.avatar_url
            existing_member.role = role
            existing_member.relation = relation
            existing_member.updated_at = datetime.utcnow()
            await self.db.flush()
            return True, existing_member, "成员已重新激活"
        
        # 创建新成员
        member = FamilyMember(
            archive_id=archive_id,
            openid=openid,
            nickname=nickname,
            avatar_url=avatar_url,
            role=role,
            relation=relation,
            notification_enabled=True,
            is_active=True
        )
        self.db.add(member)
        await self.db.flush()
        
        return True, member, "成员加入成功"
    
    async def get_members(self, archive_id: int) -> List[FamilyMember]:
        """获取档案的所有成员"""
        result = await self.db.execute(
            select(FamilyMember).where(
                and_(
                    FamilyMember.archive_id == archive_id,
                    FamilyMember.is_active == True
                )
            ).order_by(FamilyMember.joined_at)
        )
        return list(result.scalars().all())
    
    async def get_member(self, member_id: int) -> Optional[FamilyMember]:
        """获取成员信息"""
        result = await self.db.execute(
            select(FamilyMember).where(FamilyMember.id == member_id)
        )
        return result.scalar_one_or_none()
    
    async def update_member(
        self,
        member_id: int,
        **kwargs
    ) -> Optional[FamilyMember]:
        """
        更新成员信息
        
        支持更新的字段：
        - nickname: 昵称
        - avatar_url: 头像
        - role: 角色
        - relation: 与孕妇关系
        - notification_enabled: 通知开关
        """
        member = await self.get_member(member_id)
        if not member:
            return None
        
        updatable_fields = [
            'nickname', 'avatar_url', 'role', 'relation', 'notification_enabled'
        ]
        
        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(member, field, kwargs[field])
        
        member.updated_at = datetime.utcnow()
        await self.db.flush()
        
        return member
    
    async def remove_member(self, member_id: int) -> bool:
        """移除成员（软删除）"""
        member = await self.get_member(member_id)
        if not member:
            return False
        
        # 孕妇本人不能被移除
        if member.role == MemberRole.OWNER:
            return False
        
        member.is_active = False
        member.updated_at = datetime.utcnow()
        await self.db.flush()
        
        return True
    
    async def get_archive_summary(self, archive_id: int) -> Dict[str, Any]:
        """
        获取档案摘要信息
        
        包含：孕周、阶段、成员数、健康指标等
        """
        archive = await self.get_archive(archive_id)
        if not archive:
            return {}
        
        members = await self.get_members(archive_id)
        
        summary = {
            "archive_id": archive.id,
            "family_code": archive.family_code,
            "due_date": archive.due_date.isoformat() if archive.due_date else None,
            "pregnancy_weeks": archive.pregnancy_weeks,
            "pregnancy_days": archive.pregnancy_days,
            "trimester": archive.trimester,
            "stage_name": get_stage_name(archive.trimester),
            "is_high_risk": archive.is_high_risk,
            "member_count": len(members),
            "created_at": archive.created_at.isoformat() if archive.created_at else None
        }
        
        # 如果有体重身高，计算 BMI
        if archive.pre_pregnancy_weight and archive.height:
            bmi = calculate_bmi(archive.pre_pregnancy_weight, archive.height)
            summary["pre_pregnancy_bmi"] = bmi
            summary["pre_pregnancy_weight"] = archive.pre_pregnancy_weight
            summary["height"] = archive.height
            
            # 推荐体重增长
            weight_gain = get_recommended_weight_gain(
                archive.pre_pregnancy_weight,
                bmi,
                archive.pregnancy_weeks
            )
            summary["weight_gain_recommendation"] = weight_gain
        
        return summary