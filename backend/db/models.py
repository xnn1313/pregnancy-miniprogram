"""
数据模型定义
孕期小程序所有数据表模型
"""

from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, Date, DateTime, Time,
    ForeignKey, JSON, Index, UniqueConstraint, CheckConstraint,
    text, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ==================== 枚举定义 ====================

class MemberRole(str, Enum):
    """家庭成员角色"""
    OWNER = "owner"      # 孕妇本人
    PARTNER = "partner"  # 配偶/伴侣


class RecordType(str, Enum):
    """记录类型"""
    WEIGHT = "weight"       # 体重
    SYMPTOM = "symptom"     # 症状
    MOOD = "mood"           # 情绪
    DIET = "diet"           # 饮食
    NOTE = "note"           # 备注


class SymptomSeverity(str, Enum):
    """症状严重程度"""
    NONE = "none"       # 无
    MILD = "mild"       # 轻微
    MODERATE = "moderate"  # 中度
    SEVERE = "severe"   # 严重


class MoodLevel(str, Enum):
    """情绪等级"""
    GREAT = "great"     # 很好
    GOOD = "good"       # 良好
    NORMAL = "normal"   # 一般
    BAD = "bad"         # 不好
    TERRIBLE = "terrible"  # 很差


class ReminderType(str, Enum):
    """提醒类型"""
    CHECKUP = "checkup"     # 产检提醒
    MEDICINE = "medicine"  # 用药提醒
    NUTRITION = "nutrition"  # 营养提醒
    CUSTOM = "custom"       # 自定义提醒


class ReminderChannel(str, Enum):
    """提醒渠道"""
    IN_APP = "in_app"      # 站内提醒
    WECHAT = "wechat"      # 微信订阅消息
    SMS = "sms"            # 短信（预留）


class DeliveryStatus(str, Enum):
    """触达状态"""
    PENDING = "pending"     # 待发送
    SENT = "sent"           # 已发送
    DELIVERED = "delivered" # 已送达
    FAILED = "failed"       # 发送失败
    READ = "read"           # 已读


# ==================== 1. 家庭档案表 ====================

class FamilyArchive(Base):
    """
    孕期档案表
    存储家庭的基本孕期信息
    """
    __tablename__ = "family_archive"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 家庭标识
    family_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
        comment="家庭邀请码（用于加入家庭）"
    )
    
    # 孕期核心信息
    due_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="预产期"
    )
    last_period_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="末次月经日期（用于计算孕周）"
    )
    pregnancy_weeks: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="当前孕周（自动计算）"
    )
    pregnancy_days: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="当前孕周天数（0-6）"
    )
    
    # 孕期阶段
    trimester: Mapped[int] = mapped_column(
        Integer, default=1,
        comment="孕期阶段：1=早期，2=中期，3=晚期"
    )
    
    # 孕妇信息
    pre_pregnancy_weight: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="孕前体重(kg)"
    )
    height: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="身高(cm)"
    )
    age: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="年龄"
    )
    
    # 高危标记
    is_high_risk: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否高危妊娠"
    )
    high_risk_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="高危因素说明"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    members: Mapped[List["FamilyMember"]] = relationship(
        "FamilyMember", back_populates="archive", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_family_code", "family_code"),
        Index("idx_due_date", "due_date"),
    )


# ==================== 2. 家庭成员表 ====================

class FamilyMember(Base):
    """
    家庭成员表
    存储家庭成员及其角色信息
    """
    __tablename__ = "family_member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联档案
    archive_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_archive.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属家庭档案ID"
    )
    
    # 用户信息
    openid: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
        comment="微信 openid"
    )
    nickname: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="昵称"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="头像URL"
    )
    
    # 角色信息
    role: Mapped[MemberRole] = mapped_column(
        SQLEnum(MemberRole), default=MemberRole.OWNER,
        comment="角色：owner=孕妇本人，partner=配偶"
    )
    
    # 配偶信息（如果是 partner 角色）
    relation: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="与孕妇关系：husband/wife/mother/father/other"
    )
    
    # 通知设置
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="是否接收通知"
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="是否活跃成员"
    )
    
    # 时间戳
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="加入时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    archive: Mapped["FamilyArchive"] = relationship("FamilyArchive", back_populates="members")
    daily_records: Mapped[List["DailyRecord"]] = relationship(
        "DailyRecord", back_populates="member", cascade="all, delete-orphan"
    )
    custom_recipes: Mapped[List["RecipeCustom"]] = relationship(
        "RecipeCustom", back_populates="creator", cascade="all, delete-orphan"
    )
    reminder_tasks: Mapped[List["ReminderTask"]] = relationship(
        "ReminderTask", back_populates="owner", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_member_archive", "archive_id"),
        Index("idx_member_openid", "openid"),
        Index("idx_member_role", "role"),
    )


# ==================== 3. 每日记录表 ====================

class DailyRecord(Base):
    """
    每日记录表
    存储每日体重、症状、情绪、饮食等记录
    """
    __tablename__ = "daily_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联成员
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_member.id", ondelete="CASCADE"),
        nullable=False,
        comment="记录者ID"
    )
    archive_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_archive.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属家庭档案ID"
    )
    
    # 记录日期
    record_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        comment="记录日期"
    )
    
    # 体重记录
    weight: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="体重(kg)"
    )
    weight_change: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="体重变化(kg)"
    )
    
    # 症状记录
    symptom_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="症状类型：nausea/fatigue/edema/headache/backpain/cramps/other"
    )
    symptom_severity: Mapped[Optional[SymptomSeverity]] = mapped_column(
        SQLEnum(SymptomSeverity), nullable=True,
        comment="症状严重程度"
    )
    symptom_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="症状备注"
    )
    
    # 情绪记录
    mood_level: Mapped[Optional[MoodLevel]] = mapped_column(
        SQLEnum(MoodLevel), nullable=True,
        comment="情绪等级"
    )
    mood_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="情绪备注"
    )
    
    # 饮食记录
    diet_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="饮食摘要"
    )
    diet_photo_urls: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True,
        comment="饮食照片URL列表"
    )
    
    # 其他记录
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="其他备注"
    )
    
    # 营养摄入（关联当日营养汇总）
    nutrition_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("nutrition_profile_daily.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的每日营养汇总ID"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    member: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="daily_records")
    nutrition_profile: Mapped[Optional["NutritionProfileDaily"]] = relationship(
        "NutritionProfileDaily", back_populates="daily_records"
    )
    
    __table_args__ = (
        Index("idx_record_member_date", "member_id", "record_date", unique=True),
        Index("idx_record_archive_date", "archive_id", "record_date"),
        Index("idx_record_date", "record_date"),
    )


# ==================== 4. 模板食谱表 ====================

class RecipeTemplate(Base):
    """
    模板食谱表
    系统预置的孕期食谱模板
    """
    __tablename__ = "recipe_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="食谱名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="食谱描述"
    )
    
    # 分类
    category: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="分类：breakfast/lunch/dinner/snack/soup/dessert"
    )
    cuisine: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="菜系：chinese/western/japanese/korean/other"
    )
    
    # 孕期适用
    trimester_suitable: Mapped[str] = mapped_column(
        String(20), default="1,2,3",
        comment="适用孕期阶段：1=早期，2=中期，3=晚期，逗号分隔多选"
    )
    
    # 营养信息（每份）
    calories: Mapped[float] = mapped_column(
        Float, default=0,
        comment="热量(kcal)"
    )
    protein: Mapped[float] = mapped_column(
        Float, default=0,
        comment="蛋白质(g)"
    )
    carbs: Mapped[float] = mapped_column(
        Float, default=0,
        comment="碳水化合物(g)"
    )
    fat: Mapped[float] = mapped_column(
        Float, default=0,
        comment="脂肪(g)"
    )
    fiber: Mapped[float] = mapped_column(
        Float, default=0,
        comment="膳食纤维(g)"
    )
    sodium: Mapped[float] = mapped_column(
        Float, default=0,
        comment="钠(mg)"
    )
    iron: Mapped[float] = mapped_column(
        Float, default=0,
        comment="铁(mg)"
    )
    calcium: Mapped[float] = mapped_column(
        Float, default=0,
        comment="钙(mg)"
    )
    folate: Mapped[float] = mapped_column(
        Float, default=0,
        comment="叶酸(μg)"
    )
    
    # 制作信息
    prep_time: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="准备时间(分钟)"
    )
    cook_time: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="烹饪时间(分钟)"
    )
    servings: Mapped[int] = mapped_column(
        Integer, default=2,
        comment="份数"
    )
    difficulty: Mapped[int] = mapped_column(
        Integer, default=1,
        comment="难度：1=简单，2=中等，3=困难"
    )
    
    # 详细内容
    ingredients: Mapped[str] = mapped_column(
        JSON, nullable=False,
        comment="食材列表JSON: [{name, amount, unit}]"
    )
    steps: Mapped[str] = mapped_column(
        JSON, nullable=False,
        comment="制作步骤JSON: [{step_num, content, tips}]"
    )
    
    # 图片
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="食谱图片URL"
    )
    
    # 禁忌标记
    forbidden_tags: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="禁忌标签：避免某些人群"
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="是否启用"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    custom_copies: Mapped[List["RecipeCustom"]] = relationship(
        "RecipeCustom", back_populates="template_source"
    )
    ingredients_list: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe_template", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_template_category", "category"),
        Index("idx_template_trimester", "trimester_suitable"),
        Index("idx_template_active", "is_active"),
    )


# ==================== 5. 自建食谱表 ====================

class RecipeCustom(Base):
    """
    自建食谱表
    用户自定义的食谱
    """
    __tablename__ = "recipe_custom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联创建者
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_member.id", ondelete="CASCADE"),
        nullable=False,
        comment="创建者ID"
    )
    
    # 关联模板（如果是复制修改）
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recipe_template.id", ondelete="SET NULL"),
        nullable=True,
        comment="来源模板ID（如果是复制）"
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="食谱名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="食谱描述"
    )
    
    # 分类
    category: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="分类"
    )
    
    # 营养信息（可选，用户可以自己填写）
    calories: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="热量(kcal)"
    )
    protein: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="蛋白质(g)"
    )
    carbs: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="碳水化合物(g)"
    )
    fat: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="脂肪(g)"
    )
    
    # 制作信息
    prep_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="准备时间(分钟)"
    )
    cook_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="烹饪时间(分钟)"
    )
    servings: Mapped[int] = mapped_column(
        Integer, default=2,
        comment="份数"
    )
    
    # 详细内容
    ingredients: Mapped[str] = mapped_column(
        JSON, nullable=False,
        comment="食材列表JSON"
    )
    steps: Mapped[str] = mapped_column(
        JSON, nullable=False,
        comment="制作步骤JSON"
    )
    
    # 图片
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="食谱图片URL"
    )
    
    # 版本控制
    version: Mapped[int] = mapped_column(
        Integer, default=1,
        comment="版本号"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recipe_custom.id", ondelete="SET NULL"),
        nullable=True,
        comment="父版本ID（用于版本追溯）"
    )
    
    # 状态
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否已删除（软删除）"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    creator: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="custom_recipes")
    template_source: Mapped[Optional["RecipeTemplate"]] = relationship(
        "RecipeTemplate", back_populates="custom_copies"
    )
    ingredients_list: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe_custom", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_custom_creator", "creator_id"),
        Index("idx_custom_template", "template_id"),
        Index("idx_custom_category", "category"),
        Index("idx_custom_deleted", "is_deleted"),
    )


# ==================== 6. 食材明细表 ====================

class RecipeIngredient(Base):
    """
    食材明细表
    存储食谱中的食材详细信息
    """
    __tablename__ = "recipe_ingredient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联食谱（模板或自建，二选一）
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recipe_template.id", ondelete="CASCADE"),
        nullable=True,
        comment="模板食谱ID"
    )
    custom_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recipe_custom.id", ondelete="CASCADE"),
        nullable=True,
        comment="自建食谱ID"
    )
    
    # 食材信息
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="食材名称"
    )
    amount: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="用量"
    )
    unit: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="单位：g/ml/个/片/勺等"
    )
    
    # 营养信息（可选，来自 USDA 或手动输入）
    fdc_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="USDA FDC ID"
    )
    calories: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="热量(kcal)"
    )
    protein: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="蛋白质(g)"
    )
    carbs: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="碳水化合物(g)"
    )
    fat: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="脂肪(g)"
    )
    fiber: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="膳食纤维(g)"
    )
    
    # 孕期安全
    is_safe_for_pregnancy: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="孕期是否安全"
    )
    pregnancy_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="孕期注意事项"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 关联关系
    recipe_template: Mapped[Optional["RecipeTemplate"]] = relationship(
        "RecipeTemplate", back_populates="ingredients_list"
    )
    recipe_custom: Mapped[Optional["RecipeCustom"]] = relationship(
        "RecipeCustom", back_populates="ingredients_list"
    )
    
    __table_args__ = (
        Index("idx_ingredient_template", "template_id"),
        Index("idx_ingredient_custom", "custom_id"),
        Index("idx_ingredient_name", "name"),
        CheckConstraint(
            "(template_id IS NOT NULL) OR (custom_id IS NOT NULL)",
            name="ck_recipe_reference"
        ),
    )


# ==================== 7. 每日营养汇总表 ====================

class NutritionProfileDaily(Base):
    """
    每日营养汇总表
    存储每日营养摄入统计
    """
    __tablename__ = "nutrition_profile_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联档案
    archive_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_archive.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属家庭档案ID"
    )
    
    # 日期
    date: Mapped[date] = mapped_column(
        Date, nullable=False,
        comment="日期"
    )
    
    # 宏量营养素
    calories_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总热量(kcal)"
    )
    protein_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总蛋白质(g)"
    )
    carbs_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总碳水化合物(g)"
    )
    fat_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总脂肪(g)"
    )
    fiber_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总膳食纤维(g)"
    )
    
    # 微量营养素
    sodium_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总钠(mg)"
    )
    iron_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总铁(mg)"
    )
    calcium_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总钙(mg)"
    )
    folate_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总叶酸(μg)"
    )
    vitamin_d_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总维生素D(IU)"
    )
    vitamin_c_total: Mapped[float] = mapped_column(
        Float, default=0,
        comment="总维生素C(mg)"
    )
    
    # 推荐值（根据孕周动态计算）
    calories_recommended: Mapped[float] = mapped_column(
        Float, default=2000,
        comment="推荐热量(kcal)"
    )
    protein_recommended: Mapped[float] = mapped_column(
        Float, default=70,
        comment="推荐蛋白质(g)"
    )
    iron_recommended: Mapped[float] = mapped_column(
        Float, default=27,
        comment="推荐铁(mg)"
    )
    calcium_recommended: Mapped[float] = mapped_column(
        Float, default=1000,
        comment="推荐钙(mg)"
    )
    folate_recommended: Mapped[float] = mapped_column(
        Float, default=600,
        comment="推荐叶酸(μg)"
    )
    
    # 达标率
    calories_ratio: Mapped[float] = mapped_column(
        Float, default=0,
        comment="热量达标率(%)"
    )
    protein_ratio: Mapped[float] = mapped_column(
        Float, default=0,
        comment="蛋白质达标率(%)"
    )
    iron_ratio: Mapped[float] = mapped_column(
        Float, default=0,
        comment="铁达标率(%)"
    )
    calcium_ratio: Mapped[float] = mapped_column(
        Float, default=0,
        comment="钙达标率(%)"
    )
    
    # 餐食记录
    meal_count: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="用餐次数"
    )
    meals: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True,
        comment="餐食记录JSON: [{meal_type, recipe_ids, time}]"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    daily_records: Mapped[List["DailyRecord"]] = relationship(
        "DailyRecord", back_populates="nutrition_profile"
    )
    
    __table_args__ = (
        Index("idx_nutrition_archive_date", "archive_id", "date", unique=True),
        Index("idx_nutrition_date", "date"),
    )


# ==================== 8. 产检计划表 ====================

class CheckupPlan(Base):
    """
    产检计划表
    存储预定的产检计划
    """
    __tablename__ = "checkup_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联档案
    archive_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_archive.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属家庭档案ID"
    )
    
    # 产检信息
    checkup_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="产检类型：routine/nt/big_4d/glucose/blood/urine/other"
    )
    checkup_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="产检名称"
    )
    
    # 计划时间
    planned_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        comment="计划日期"
    )
    planned_time: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True,
        comment="计划时间"
    )
    
    # 医院/医生
    hospital: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="医院名称"
    )
    doctor: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="医生姓名"
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="科室"
    )
    
    # 检查项目
    items: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True,
        comment="检查项目列表JSON: [{name, description}]"
    )
    
    # 注意事项
    preparation_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="准备事项（空腹、憋尿等）"
    )
    
    # 孕周范围
    week_start: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="建议孕周起始"
    )
    week_end: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="建议孕周结束"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default="planned",
        comment="状态：planned/completed/cancelled/rescheduled"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    results: Mapped[List["CheckupResult"]] = relationship(
        "CheckupResult", back_populates="plan", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_checkup_archive", "archive_id"),
        Index("idx_checkup_date", "planned_date"),
        Index("idx_checkup_status", "status"),
    )


# ==================== 9. 产检结果表 ====================

class CheckupResult(Base):
    """
    产检结果表
    存储产检的实际结果
    """
    __tablename__ = "checkup_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联计划
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("checkup_plan.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的产检计划ID"
    )
    archive_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_archive.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属家庭档案ID"
    )
    
    # 实际时间
    actual_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        comment="实际检查日期"
    )
    
    # 结果数据
    result_data: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True,
        comment="检查结果数据JSON: [{item, value, unit, reference_range, is_abnormal}]"
    )
    
    # 汇总
    is_abnormal: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否有异常"
    )
    abnormal_items: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="异常项目描述"
    )
    
    # 医生意见
    doctor_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="医生意见"
    )
    
    # 建议
    suggestions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="建议（复查、注意事项等）"
    )
    
    # 复查
    needs_followup: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否需要复查"
    )
    followup_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="建议复查日期"
    )
    
    # 附件
    attachment_urls: Mapped[Optional[str]] = mapped_column(
        JSON, nullable=True,
        comment="附件URL列表（报告单照片等）"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    plan: Mapped["CheckupPlan"] = relationship("CheckupPlan", back_populates="results")
    
    __table_args__ = (
        Index("idx_result_plan", "plan_id"),
        Index("idx_result_archive", "archive_id"),
        Index("idx_result_date", "actual_date"),
        Index("idx_result_abnormal", "is_abnormal"),
    )


# ==================== 10. 提醒任务表 ====================

class ReminderTask(Base):
    """
    提醒任务表
    存储提醒任务配置
    """
    __tablename__ = "reminder_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联用户
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_member.id", ondelete="CASCADE"),
        nullable=False,
        comment="提醒接收者ID"
    )
    archive_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_archive.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属家庭档案ID"
    )
    
    # 关联产检（如果是产检提醒）
    checkup_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("checkup_plan.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联产检计划ID"
    )
    
    # 提醒信息
    title: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="提醒标题"
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="提醒内容"
    )
    
    # 提醒类型
    reminder_type: Mapped[ReminderType] = mapped_column(
        SQLEnum(ReminderType), default=ReminderType.CUSTOM,
        comment="提醒类型"
    )
    
    # 触发时间
    trigger_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        comment="触发日期"
    )
    trigger_time: Mapped[time] = mapped_column(
        Time, nullable=False,
        comment="触发时间"
    )
    
    # 重复设置
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否重复"
    )
    recurring_pattern: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="重复模式：daily/weekly/monthly"
    )
    recurring_end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="重复结束日期"
    )
    
    # 提醒渠道
    channels: Mapped[str] = mapped_column(
        String(100), default="in_app",
        comment="提醒渠道：逗号分隔多个渠道"
    )
    
    # 提前提醒
    advance_minutes: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="提前多少分钟提醒"
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="是否启用"
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="上次触发时间"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    owner: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="reminder_tasks")
    deliveries: Mapped[List["ReminderDelivery"]] = relationship(
        "ReminderDelivery", back_populates="task", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_reminder_owner", "owner_id"),
        Index("idx_reminder_archive", "archive_id"),
        Index("idx_reminder_date", "trigger_date"),
        Index("idx_reminder_active", "is_active"),
    )


# ==================== 11. 提醒触达流水表 ====================

class ReminderDelivery(Base):
    """
    提醒触达流水表
    记录每次提醒的发送状态
    """
    __tablename__ = "reminder_delivery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联任务
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reminder_task.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联提醒任务ID"
    )
    
    # 渠道
    channel: Mapped[ReminderChannel] = mapped_column(
        SQLEnum(ReminderChannel), default=ReminderChannel.IN_APP,
        comment="触达渠道"
    )
    
    # 发送信息
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        comment="计划发送时间"
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="实际发送时间"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="送达时间"
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="阅读时间"
    )
    
    # 状态
    status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING,
        comment="触达状态"
    )
    
    # 失败信息
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="错误码"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="错误信息"
    )
    
    # 重试
    retry_count: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="重试次数"
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="下次重试时间"
    )
    
    # 外部ID（用于追踪）
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="外部消息ID（微信消息ID等）"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关联关系
    task: Mapped["ReminderTask"] = relationship("ReminderTask", back_populates="deliveries")
    
    __table_args__ = (
        Index("idx_delivery_task", "task_id"),
        Index("idx_delivery_scheduled", "scheduled_at"),
        Index("idx_delivery_status", "status"),
        Index("idx_delivery_channel", "channel"),
    )