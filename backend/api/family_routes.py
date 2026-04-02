"""
家庭 API 路由
对接 family_service 实现完整功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.family_service import (
    FamilyService, PermissionChecker,
    calculate_pregnancy_week, get_trimester, get_stage_name,
    calculate_bmi, get_recommended_weight_gain
)

router = APIRouter(prefix="/api/v1/family", tags=["家庭"])


# ==================== 请求模型 ====================

class ArchiveCreate(BaseModel):
    """创建档案请求"""
    openid: str = Field(..., description="用户 openid")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    due_date: Optional[str] = Field(None, description="预产期 YYYY-MM-DD")
    last_period_date: Optional[str] = Field(None, description="末次月经日期 YYYY-MM-DD")
    pre_pregnancy_weight: Optional[float] = Field(None, ge=30, le=200, description="孕前体重(kg)")
    height: Optional[float] = Field(None, ge=100, le=250, description="身高(cm)")
    age: Optional[int] = Field(None, ge=18, le=50, description="年龄")


class ArchiveUpdate(BaseModel):
    """更新档案请求"""
    archive_id: int = Field(..., description="档案ID")
    due_date: Optional[str] = Field(None, description="预产期")
    last_period_date: Optional[str] = Field(None, description="末次月经日期")
    pre_pregnancy_weight: Optional[float] = Field(None, description="孕前体重")
    height: Optional[float] = Field(None, description="身高")
    age: Optional[int] = Field(None, description="年龄")
    is_high_risk: Optional[bool] = Field(None, description="是否高危")
    high_risk_notes: Optional[str] = Field(None, description="高危因素")


class MemberInvite(BaseModel):
    """邀请成员请求"""
    archive_id: int = Field(..., description="档案ID")
    openid: str = Field(..., description="新成员 openid")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    role: Optional[str] = Field("partner", description="角色: owner/partner")
    relation: Optional[str] = Field(None, description="关系: husband/wife/mother/father/other")


class JoinByCode(BaseModel):
    """通过邀请码加入"""
    family_code: str = Field(..., min_length=6, max_length=6, description="家庭邀请码")
    openid: str = Field(..., description="用户 openid")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    relation: Optional[str] = Field(None, description="关系")


# ==================== API 接口 ====================

@router.post("/archive")
async def create_archive(
    request: ArchiveCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建家庭档案
    
    创建时自动创建孕妇本人的成员记录
    """
    service = FamilyService(db)
    
    # 解析日期
    due_date = None
    last_period = None
    
    if request.due_date:
        try:
            due_date = date.fromisoformat(request.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="预产期格式错误")
    
    if request.last_period_date:
        try:
            last_period = date.fromisoformat(request.last_period_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="末次月经日期格式错误")
    
    try:
        archive, member = await service.create_archive(
            openid=request.openid,
            nickname=request.nickname,
            avatar_url=request.avatar_url,
            due_date=due_date,
            last_period_date=last_period,
            pre_pregnancy_weight=request.pre_pregnancy_weight,
            height=request.height,
            age=request.age
        )
        
        await db.commit()
        
        return {
            "success": True,
            "archive_id": archive.id,
            "member_id": member.id,
            "family_code": archive.family_code,
            "pregnancy_week": archive.pregnancy_weeks,
            "trimester": archive.trimester,
            "message": "档案创建成功"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建档案失败: {str(e)}")


@router.get("/archive")
async def get_archive(
    archive_id: Optional[int] = Query(None, description="档案ID"),
    openid: Optional[str] = Query(None, description="用户openid（二选一）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取档案信息
    
    可通过档案ID或用户openid查询
    """
    service = FamilyService(db)
    
    try:
        archive = None
        
        if archive_id:
            archive = await service.get_archive(archive_id)
        elif openid:
            archive = await service.get_archive_by_openid(openid)
        else:
            raise HTTPException(status_code=400, detail="需要提供 archive_id 或 openid")
        
        if not archive:
            raise HTTPException(status_code=404, detail="档案不存在")
        
        # 计算BMI（如果有身高体重）
        bmi = None
        bmi_category = None
        if archive.pre_pregnancy_weight and archive.height:
            bmi = calculate_bmi(archive.pre_pregnancy_weight, archive.height)
            if bmi < 18.5:
                bmi_category = "偏瘦"
            elif bmi < 24:
                bmi_category = "正常"
            elif bmi < 28:
                bmi_category = "超重"
            else:
                bmi_category = "肥胖"
        
        # 计算推荐体重增长
        weight_recommendation = None
        if archive.pre_pregnancy_weight and archive.height and archive.pregnancy_weeks:
            weight_recommendation = get_recommended_weight_gain(
                archive.pre_pregnancy_weight,
                bmi,
                archive.pregnancy_weeks
            )
        
        return {
            "id": archive.id,
            "family_code": archive.family_code,
            "due_date": archive.due_date.isoformat() if archive.due_date else None,
            "last_period_date": archive.last_period_date.isoformat() if archive.last_period_date else None,
            "pregnancy_weeks": archive.pregnancy_weeks,
            "pregnancy_days": archive.pregnancy_days,
            "week_display": f"{archive.pregnancy_weeks}周+{archive.pregnancy_days}天",
            "trimester": archive.trimester,
            "stage_name": get_stage_name(archive.trimester),
            "pre_pregnancy_weight": archive.pre_pregnancy_weight,
            "height": archive.height,
            "age": archive.age,
            "bmi": bmi,
            "bmi_category": bmi_category,
            "is_high_risk": archive.is_high_risk,
            "high_risk_notes": archive.high_risk_notes,
            "weight_recommendation": weight_recommendation,
            "created_at": archive.created_at.isoformat() if archive.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取档案失败: {str(e)}")


@router.put("/archive")
async def update_archive(
    request: ArchiveUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新档案信息
    """
    service = FamilyService(db)
    
    # 解析日期
    kwargs = {"archive_id": request.archive_id}
    
    if request.due_date:
        try:
            kwargs["due_date"] = date.fromisoformat(request.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="预产期格式错误")
    
    if request.last_period_date:
        try:
            kwargs["last_period_date"] = date.fromisoformat(request.last_period_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="末次月经日期格式错误")
    
    if request.pre_pregnancy_weight:
        kwargs["pre_pregnancy_weight"] = request.pre_pregnancy_weight
    if request.height:
        kwargs["height"] = request.height
    if request.age:
        kwargs["age"] = request.age
    if request.is_high_risk is not None:
        kwargs["is_high_risk"] = request.is_high_risk
    if request.high_risk_notes:
        kwargs["high_risk_notes"] = request.high_risk_notes
    
    try:
        archive = await service.update_archive(**kwargs)
        
        if not archive:
            raise HTTPException(status_code=404, detail="档案不存在")
        
        await db.commit()
        
        return {
            "success": True,
            "archive_id": archive.id,
            "pregnancy_weeks": archive.pregnancy_weeks,
            "trimester": archive.trimester,
            "message": "档案更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新档案失败: {str(e)}")


@router.post("/member")
async def invite_member(
    request: MemberInvite,
    db: AsyncSession = Depends(get_db)
):
    """
    邀请成员加入家庭
    """
    service = FamilyService(db)
    
    from ..db.models import MemberRole
    
    try:
        role = MemberRole.PARTNER
        if request.role == "owner":
            role = MemberRole.OWNER
        
        success, member, message = await service.invite_member(
            archive_id=request.archive_id,
            openid=request.openid,
            nickname=request.nickname,
            avatar_url=request.avatar_url,
            role=role,
            relation=request.relation
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        await db.commit()
        
        return {
            "success": True,
            "member_id": member.id,
            "role": member.role.value,
            "message": "成员邀请成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"邀请成员失败: {str(e)}")


@router.post("/join")
async def join_by_code(
    request: JoinByCode,
    db: AsyncSession = Depends(get_db)
):
    """
    通过邀请码加入家庭
    """
    service = FamilyService(db)
    
    try:
        success, archive, member, message = await service.join_family_by_code(
            family_code=request.family_code,
            openid=request.openid,
            nickname=request.nickname,
            avatar_url=request.avatar_url,
            relation=request.relation
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        await db.commit()
        
        return {
            "success": True,
            "archive_id": archive.id,
            "member_id": member.id,
            "family_code": archive.family_code,
            "message": "加入家庭成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"加入家庭失败: {str(e)}")


@router.get("/members")
async def list_members(
    archive_id: int = Query(..., description="档案ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取家庭成员列表
    """
    service = FamilyService(db)
    
    try:
        members = await service.get_members(archive_id)
        
        return {
            "members": [
                {
                    "id": m.id,
                    "openid": m.openid,
                    "nickname": m.nickname,
                    "avatar_url": m.avatar_url,
                    "role": m.role.value,
                    "relation": m.relation,
                    "notification_enabled": m.notification_enabled,
                    "is_active": m.is_active,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None
                }
                for m in members
            ],
            "total": len(members)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成员列表失败: {str(e)}")


@router.delete("/member/{member_id}")
async def remove_member(
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    移除家庭成员（软删除）
    """
    service = FamilyService(db)
    
    try:
        success = await service.remove_member(member_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        await db.commit()
        
        return {
            "success": True,
            "message": "成员已移除"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"移除成员失败: {str(e)}")


@router.get("/pregnancy-info")
async def get_pregnancy_info(
    due_date: str = Query(..., description="预产期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取孕期信息（根据预产期计算）
    
    用于快速查询孕周信息，无需档案
    """
    try:
        due = date.fromisoformat(due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="预产期格式错误")
    
    weeks, days = calculate_pregnancy_week(due)
    trimester = get_trimester(weeks)
    
    return {
        "due_date": due_date,
        "pregnancy_weeks": weeks,
        "pregnancy_days": days,
        "week_display": f"{weeks}周+{days}天",
        "trimester": trimester,
        "stage_name": get_stage_name(trimester),
        "days_to_due": (due - date.today()).days
    }