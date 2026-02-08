from datetime import timezone as dt_timezone
from django.utils import timezone

from points_record.mapper.points_record_mapper import PointsRecordMapper


class PointsRecordError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class PointsRecordService:
    def __init__(self):
        self.mapper = PointsRecordMapper()

    def get_points_summary(self, user):
        try:
            summary = self.mapper.get_points_summary(user)
            return {
                "user": {
                    "id": self._public_user_id(user.id),
                    "nickname": user.nickname,
                    "points": user.points,
                    "activity_points": user.activity_points,
                },
                "summary": summary,
            }
        except Exception as exc:
            raise PointsRecordError(500, f"Internal server error: {str(exc)}")

    def list_points_logs(self, user, filters):
        normalized = self._normalize_filters(filters)
        queryset = self.mapper.list_points_logs(user, normalized)
        total = queryset.count()

        page = max(normalized.get("page", 1), 1)
        page_size = min(max(normalized.get("page_size", 20), 1), 50)
        offset = (page - 1) * page_size

        ordering = self._ordering_for_sort(normalized.get("sort"))
        logs = list(queryset.order_by(*ordering)[offset : offset + page_size])

        items = [
            self._to_points_log_item(log)
            for log in logs
        ]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def _normalize_filters(self, filters):
        return {
            "type": (filters.get("type") or "").strip(),
            "start_date": filters.get("start_date"),
            "end_date": filters.get("end_date"),
            "keyword": (filters.get("keyword") or "").strip(),
            "sort": (filters.get("sort") or "").strip(),
            "page": filters.get("page", 1),
            "page_size": filters.get("page_size", 20),
        }

    def _ordering_for_sort(self, sort):
        if sort == "time_asc":
            return ("created_at",)
        if sort == "amount_desc":
            return ("-delta", "-created_at")
        if sort == "amount_asc":
            return ("delta", "-created_at")
        # 默认按时间倒序
        return ("-created_at",)

    def _to_points_log_item(self, log):
        return {
            "id": str(log.id),
            "type": log.points_type,
            "delta": log.delta,
            "balance": 0,  # 需要在controller中计算
            "reason": log.reason,
            "ref_type": log.ref_type,
            "ref_id": log.ref_id,
            "created_at": self._iso_str(log.created_at),
        }

    def _public_user_id(self, user_id):
        return f"u_{user_id}"

    def _iso_str(self, dt):
        if not dt:
            return None
        return dt.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")

    def update_points(self, user, delta, reason, ref_type=None, ref_id=None):
        try:
            # 验证参数
            if not isinstance(delta, int):
                raise PointsRecordError(400, "Invalid delta value")
            if not reason:
                raise PointsRecordError(400, "Reason is required")
            
            # 检查积分是否足够（如果是减少积分）
            if delta < 0 and user.points < abs(delta):
                raise PointsRecordError(400, "Insufficient points")
            
            # 更新用户积分
            user.points += delta
            # 如果是增加积分，同时增加活跃度积分
            if delta > 0:
                user.activity_points += delta
            user.save()
            
            # 创建积分变更记录
            points_log = self.mapper.create_points_log(
                user=user,
                points_type=ref_type or "other",
                delta=delta,
                reason=reason,
                ref_type=ref_type,
                ref_id=ref_id
            )
            
            # 返回更新后的信息
            return {
                "user": {
                    "id": self._public_user_id(user.id),
                    "nickname": user.nickname,
                    "points": user.points,
                    "activity_points": user.activity_points
                },
                "log": {
                    "id": str(points_log.id),
                    "type": points_log.points_type,
                    "delta": points_log.delta,
                    "reason": points_log.reason,
                    "created_at": self._iso_str(points_log.created_at)
                }
            }
        except PointsRecordError:
            raise
        except Exception as exc:
            raise PointsRecordError(500, f"Internal server error: {str(exc)}")
