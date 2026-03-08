from django.db.models import Q

from core.models import PointsLog


class PointsRecordMapper:
    @staticmethod
    def base_queryset():
        return PointsLog.objects.select_related('user')

    @staticmethod
    def list_points_logs(user, filters):
        queryset = PointsRecordMapper._apply_filters(PointsRecordMapper.base_queryset(), user, filters)
        return queryset

    @staticmethod
    def _apply_filters(queryset, user, filters):
        # 只查询当前用户的积分记录
        queryset = queryset.filter(user=user)
        
        # 应用类型过滤
        points_type = filters.get('type')
        if points_type == 'earn':
            queryset = queryset.filter(delta__gt=0)
        elif points_type == 'spend':
            queryset = queryset.filter(delta__lt=0)
        elif points_type and points_type.strip():  # 确保非空字符串
            queryset = queryset.filter(points_type=points_type)
        
        # 应用时间范围过滤
        start_date = filters.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        end_date = filters.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # 应用关键词过滤
        keyword = filters.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(reason__icontains=keyword)
            )
        
        return queryset

    @staticmethod
    def get_points_summary(user):
        # 获取用户积分汇总信息
        total_points = user.points
        total_activity_points = user.activity_points
        
        # 计算近期积分变化
        recent_logs = PointsLog.objects.filter(user=user).order_by('-created_at')[:30]
        recent_earned = sum(log.delta for log in recent_logs if log.delta > 0)
        recent_spent = sum(abs(log.delta) for log in recent_logs if log.delta < 0)
        
        return {
            'total_points': total_points,
            'total_activity_points': total_activity_points,
            'recent_earned': recent_earned,
            'recent_spent': recent_spent
        }

    @staticmethod
    def create_points_log(user, points_type, delta, reason, ref_type=None, ref_id=None):
        # 创建积分变更记录
        points_log = PointsLog.objects.create(
            user=user,
            points_type=points_type,
            delta=delta,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id
        )
        return points_log
