"""
每日记录业务逻辑服务
提供体重趋势、症状统计、情绪分析等功能
"""

from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from ..db.database import async_session_maker
from ..db.models import (
    DailyRecord, FamilyMember, FamilyArchive,
    SymptomSeverity, MoodLevel
)


class RecordService:
    """每日记录业务服务"""
    
    # 症状类型中文名映射
    SYMPTOM_NAMES = {
        "nausea": "恶心/孕吐",
        "fatigue": "疲劳",
        "edema": "水肿",
        "headache": "头痛",
        "backpain": "腰痛",
        "cramps": "抽筋",
        "insomnia": "失眠",
        "heartburn": "烧心",
        "constipation": "便秘",
        "dizziness": "头晕",
        "other": "其他"
    }
    
    # 情绪等级中文名映射
    MOOD_NAMES = {
        "great": "很好",
        "good": "良好",
        "normal": "一般",
        "bad": "不好",
        "terrible": "很差"
    }
    
    # 孕期各阶段体重增长建议（kg）
    WEIGHT_GAIN_RECOMMENDATIONS = {
        1: {"min": 0.5, "max": 2.0},   # 孕早期
        2: {"min": 2.0, "max": 5.0},   # 孕中期
        3: {"min": 5.0, "max": 12.0},  # 孕晚期
    }

    async def create_or_update_record(
        self,
        db: AsyncSession,
        member_id: int,
        archive_id: int,
        record_date: date,
        **kwargs
    ) -> DailyRecord:
        """
        创建或更新每日记录
        
        Args:
            db: 数据库会话
            member_id: 成员ID
            archive_id: 档案ID
            record_date: 记录日期
            **kwargs: 记录字段（weight, symptom_type, mood_level等）
        
        Returns:
            DailyRecord: 创建或更新的记录
        """
        # 查找是否已有记录
        stmt = select(DailyRecord).where(
            and_(
                DailyRecord.member_id == member_id,
                DailyRecord.record_date == record_date
            )
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            # 更新现有记录
            for key, value in kwargs.items():
                if value is not None and hasattr(record, key):
                    setattr(record, key, value)
            record.updated_at = date.today()
        else:
            # 创建新记录
            record = DailyRecord(
                member_id=member_id,
                archive_id=archive_id,
                record_date=record_date,
                **kwargs
            )
            db.add(record)
        
        await db.commit()
        await db.refresh(record)
        return record

    async def get_today_record(
        self,
        db: AsyncSession,
        member_id: int
    ) -> Optional[DailyRecord]:
        """
        获取今日记录
        
        Args:
            db: 数据库会话
            member_id: 成员ID
        
        Returns:
            Optional[DailyRecord]: 今日记录或None
        """
        today = date.today()
        stmt = select(DailyRecord).where(
            and_(
                DailyRecord.member_id == member_id,
                DailyRecord.record_date == today
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_record_history(
        self,
        db: AsyncSession,
        member_id: int,
        page: int = 1,
        page_size: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取历史记录（分页）
        
        Args:
            db: 数据库会话
            member_id: 成员ID
            page: 页码
            page_size: 每页数量
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            Dict: 包含记录列表和分页信息
        """
        # 构建查询条件
        conditions = [DailyRecord.member_id == member_id]
        
        if start_date:
            conditions.append(DailyRecord.record_date >= start_date)
        if end_date:
            conditions.append(DailyRecord.record_date <= end_date)
        
        # 查询总数
        count_stmt = select(func.count()).select_from(DailyRecord).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        stmt = select(DailyRecord).where(and_(*conditions)).order_by(
            DailyRecord.record_date.desc()
        ).offset(offset).limit(page_size)
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        return {
            "records": records,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def get_weight_trend(
        self,
        db: AsyncSession,
        member_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取体重趋势
        
        Args:
            db: 数据库会话
            member_id: 成员ID
            days: 查询天数
        
        Returns:
            Dict: 包含体重趋势数据和建议
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 查询体重记录
        stmt = select(DailyRecord).where(
            and_(
                DailyRecord.member_id == member_id,
                DailyRecord.record_date >= start_date,
                DailyRecord.record_date <= end_date,
                DailyRecord.weight.isnot(None)
            )
        ).order_by(DailyRecord.record_date)
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        # 构建趋势数据
        trend_data = []
        weights = []
        for record in records:
            trend_data.append({
                "date": record.record_date.isoformat(),
                "weight": record.weight,
                "change": record.weight_change
            })
            if record.weight:
                weights.append(record.weight)
        
        # 计算统计信息
        stats = {}
        if weights:
            stats = {
                "current_weight": weights[-1] if weights else None,
                "max_weight": max(weights),
                "min_weight": min(weights),
                "avg_weight": round(sum(weights) / len(weights), 1),
                "total_change": round(weights[-1] - weights[0], 1) if len(weights) > 1 else 0
            }
        
        # 获取孕期信息用于建议
        member_stmt = select(FamilyMember).where(FamilyMember.id == member_id)
        member_result = await db.execute(member_stmt)
        member = member_result.scalar_one_or_none()
        
        # 获取预产期和孕前体重
        recommendation = None
        if member:
            archive_stmt = select(FamilyArchive).where(FamilyArchive.id == member.archive_id)
            archive_result = await db.execute(archive_stmt)
            archive = archive_result.scalar_one_or_none()
            
            if archive and archive.pre_pregnancy_weight and weights:
                # 计算总体重增长
                current_weight = weights[-1]
                total_gain = current_weight - archive.pre_pregnancy_weight
                trimester = archive.trimester
                
                rec = self.WEIGHT_GAIN_RECOMMENDATIONS.get(trimester, {"min": 0, "max": 15})
                
                recommendation = {
                    "pre_pregnancy_weight": archive.pre_pregnancy_weight,
                    "total_gain": round(total_gain, 1),
                    "trimester": trimester,
                    "recommended_range": rec,
                    "is_in_range": rec["min"] <= total_gain <= rec["max"],
                    "advice": self._generate_weight_advice(total_gain, trimester, rec)
                }
        
        return {
            "trend": trend_data,
            "stats": stats,
            "recommendation": recommendation
        }

    def _generate_weight_advice(
        self,
        total_gain: float,
        trimester: int,
        recommended_range: Dict[str, float]
    ) -> str:
        """生成体重建议"""
        min_gain, max_gain = recommended_range["min"], recommended_range["max"]
        
        if total_gain < min_gain:
            return f"体重增长偏少，建议适当增加营养摄入，保证优质蛋白质和健康脂肪的摄入。当前增长{total_gain}kg，建议范围{min_gain}-{max_gain}kg。"
        elif total_gain > max_gain:
            return f"体重增长偏多，建议控制饮食热量，适当增加运动。当前增长{total_gain}kg，建议范围{min_gain}-{max_gain}kg。"
        else:
            return f"体重增长正常，继续保持均衡饮食。当前增长{total_gain}kg，在建议范围{min_gain}-{max_gain}kg内。"

    async def get_symptom_stats(
        self,
        db: AsyncSession,
        member_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取症状统计
        
        Args:
            db: 数据库会话
            member_id: 成员ID
            days: 查询天数
        
        Returns:
            Dict: 包含症状统计数据
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 查询症状记录
        stmt = select(DailyRecord).where(
            and_(
                DailyRecord.member_id == member_id,
                DailyRecord.record_date >= start_date,
                DailyRecord.record_date <= end_date,
                DailyRecord.symptom_type.isnot(None)
            )
        )
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        # 统计症状类型
        symptom_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        daily_symptoms = []
        
        for record in records:
            if record.symptom_type:
                symptom_counts[record.symptom_type] += 1
                if record.symptom_severity:
                    severity_counts[record.symptom_severity.value] += 1
                
                daily_symptoms.append({
                    "date": record.record_date.isoformat(),
                    "type": record.symptom_type,
                    "type_name": self.SYMPTOM_NAMES.get(record.symptom_type, record.symptom_type),
                    "severity": record.symptom_severity.value if record.symptom_severity else None,
                    "notes": record.symptom_notes
                })
        
        # 计算最常见症状
        top_symptoms = sorted(
            symptom_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "period_days": days,
            "total_records": len(records),
            "symptom_distribution": {
                self.SYMPTOM_NAMES.get(k, k): v 
                for k, v in symptom_counts.items()
            },
            "severity_distribution": dict(severity_counts),
            "top_symptoms": [
                {
                    "type": k,
                    "name": self.SYMPTOM_NAMES.get(k, k),
                    "count": v
                }
                for k, v in top_symptoms
            ],
            "daily_symptoms": daily_symptoms,
            "symptom_names": self.SYMPTOM_NAMES
        }

    async def get_mood_analysis(
        self,
        db: AsyncSession,
        member_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取情绪分析
        
        Args:
            db: 数据库会话
            member_id: 成员ID
            days: 查询天数
        
        Returns:
            Dict: 包含情绪分析数据
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # 查询情绪记录
        stmt = select(DailyRecord).where(
            and_(
                DailyRecord.member_id == member_id,
                DailyRecord.record_date >= start_date,
                DailyRecord.record_date <= end_date,
                DailyRecord.mood_level.isnot(None)
            )
        ).order_by(DailyRecord.record_date)
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        # 统计情绪分布
        mood_counts = defaultdict(int)
        mood_trend = []
        mood_notes = []
        
        for record in records:
            mood_value = record.mood_level.value if record.mood_level else None
            if mood_value:
                mood_counts[mood_value] += 1
                
                mood_trend.append({
                    "date": record.record_date.isoformat(),
                    "level": mood_value,
                    "level_name": self.MOOD_NAMES.get(mood_value, mood_value)
                })
                
                if record.mood_notes:
                    mood_notes.append({
                        "date": record.record_date.isoformat(),
                        "level": mood_value,
                        "notes": record.mood_notes
                    })
        
        # 计算情绪评分（很好=5, 良好=4, 一般=3, 不好=2, 很差=1）
        mood_scores = {
            "great": 5, "good": 4, "normal": 3, "bad": 2, "terrible": 1
        }
        
        total_score = sum(
            mood_counts.get(level, 0) * score 
            for level, score in mood_scores.items()
        )
        total_count = sum(mood_counts.values())
        avg_score = round(total_score / total_count, 2) if total_count > 0 else 0
        
        # 情绪状态判断
        if avg_score >= 4:
            mood_status = "积极"
            mood_advice = "你的情绪状态很好，继续保持积极心态，这对宝宝的健康成长很有帮助！"
        elif avg_score >= 3:
            mood_status = "稳定"
            mood_advice = "情绪状态良好，可以尝试一些放松活动，如听音乐、散步等。"
        elif avg_score >= 2:
            mood_status = "波动"
            mood_advice = "近期情绪波动较大，建议多与家人沟通，必要时可寻求专业心理支持。"
        else:
            mood_status = "低落"
            mood_advice = "情绪状态不佳，请务必与医生或心理咨询师沟通，获得专业帮助。"
        
        return {
            "period_days": days,
            "total_records": total_count,
            "mood_distribution": {
                self.MOOD_NAMES.get(k, k): v 
                for k, v in mood_counts.items()
            },
            "mood_trend": mood_trend,
            "mood_notes": mood_notes,
            "average_score": avg_score,
            "mood_status": mood_status,
            "mood_advice": mood_advice,
            "mood_names": self.MOOD_NAMES
        }

    async def get_record_stats(
        self,
        db: AsyncSession,
        member_id: int
    ) -> Dict[str, Any]:
        """
        获取记录统计概览
        
        Args:
            db: 数据库会话
            member_id: 成员ID
        
        Returns:
            Dict: 统计概览数据
        """
        today = date.today()
        
        # 总记录数
        total_stmt = select(func.count()).select_from(DailyRecord).where(
            DailyRecord.member_id == member_id
        )
        total_result = await db.execute(total_stmt)
        total_records = total_result.scalar()
        
        # 本月记录数
        month_start = today.replace(day=1)
        month_stmt = select(func.count()).select_from(DailyRecord).where(
            and_(
                DailyRecord.member_id == member_id,
                DailyRecord.record_date >= month_start
            )
        )
        month_result = await db.execute(month_stmt)
        month_records = month_result.scalar()
        
        # 连续记录天数
        streak = await self._calculate_streak(db, member_id)
        
        # 获取最新记录
        latest_stmt = select(DailyRecord).where(
            DailyRecord.member_id == member_id
        ).order_by(DailyRecord.record_date.desc()).limit(1)
        latest_result = await db.execute(latest_stmt)
        latest_record = latest_result.scalar_one_or_none()
        
        return {
            "total_records": total_records,
            "month_records": month_records,
            "streak_days": streak,
            "latest_record_date": latest_record.record_date.isoformat() if latest_record else None,
            "has_record_today": latest_record.record_date == today if latest_record else False
        }

    async def _calculate_streak(
        self,
        db: AsyncSession,
        member_id: int
    ) -> int:
        """计算连续记录天数"""
        today = date.today()
        streak = 0
        current_date = today
        
        while True:
            stmt = select(DailyRecord).where(
                and_(
                    DailyRecord.member_id == member_id,
                    DailyRecord.record_date == current_date
                )
            )
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if record:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak

    async def get_combined_stats(
        self,
        db: AsyncSession,
        member_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取综合统计（体重趋势+症状统计+情绪分析）
        
        Args:
            db: 数据库会话
            member_id: 成员ID
            days: 查询天数
        
        Returns:
            Dict: 综合统计数据
        """
        # 并行获取各项统计
        weight_trend = await self.get_weight_trend(db, member_id, days)
        symptom_stats = await self.get_symptom_stats(db, member_id, days)
        mood_analysis = await self.get_mood_analysis(db, member_id, days)
        record_stats = await self.get_record_stats(db, member_id)
        
        return {
            "period_days": days,
            "record_stats": record_stats,
            "weight": weight_trend,
            "symptoms": symptom_stats,
            "mood": mood_analysis
        }


# 全局服务实例
_record_service: Optional[RecordService] = None


def get_record_service() -> RecordService:
    """获取记录服务实例"""
    global _record_service
    if _record_service is None:
        _record_service = RecordService()
    return _record_service