from django.contrib.auth.hashers import check_password
import json
import logging
import secrets
from datetime import datetime, timedelta

from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.models import (
    AppUser,
    AuditLog,
    AuthCredential,
    AuthToken,
    Message,
    PointsLog,
    Questionnaire,
    RecommendationClaim,
    Response,
    Role,
    Survey,
    TaskCompletion,
    UserBehaviorLog,
    UserRole,
)
from core.views import error, get_current_user, internal_error, parse_json
from task_hall.service.level_service import LevelService

logger = logging.getLogger(__name__)


def parse_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def require_admin(request):
    user = get_current_user(request)
    if not user:
        return None, error(401, "请先登录")
    is_admin = UserRole.objects.filter(user=user, role__name="admin").exists()
    if not is_admin:
        return None, error(403, "需要管理员权限")
    return user, None


@csrf_exempt
def admin_login(request):
    if request.method != "POST":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return error(400, "邮箱和密码不能为空")

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return error(401, "邮箱或密码错误")

    is_admin = UserRole.objects.filter(user=user, role__name="admin").exists()
    if not is_admin:
        return error(403, "该账户不是管理员")

    try:
        cred = AuthCredential.objects.get(user=user)
    except AuthCredential.DoesNotExist:
        return error(401, "邮箱或密码错误")

    if not check_password(password, cred.password_hash):
        return error(401, "邮箱或密码错误")

    AuthToken.objects.filter(user=user).delete()
    token = secrets.token_urlsafe(24)
    expires_at = timezone.now() + timedelta(days=7)
    AuthToken.objects.create(user=user, token=token, expires_at=expires_at)

    return JsonResponse(
        {
            "token": token,
            "user": {
                "id": user.id,
                "nickname": user.nickname,
                "email": user.email,
            },
        }
    )


@csrf_exempt
def dashboard_stats(request):
    user, err = require_admin(request)
    if err:
        return err

    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))

    total_users = AppUser.objects.count()
    today_new_users = AppUser.objects.filter(created_at__gte=today_start).count()
    active_users_7d = (
        AuthToken.objects.filter(created_at__gte=timezone.now() - timedelta(days=7))
        .values("user_id")
        .distinct()
        .count()
    )

    total_surveys = Survey.objects.count()
    today_new_surveys = Survey.objects.filter(created_at__gte=today_start).count()
    published_surveys = Survey.objects.filter(status="published").count()

    total_fills = Response.objects.count()
    today_fills = Response.objects.filter(created_at__gte=today_start).count()

    total_points_issued = (
        PointsLog.objects.filter(delta__gt=0).aggregate(total=models.Sum("delta"))[
            "total"
        ]
        or 0
    )
    total_points_consumed = (
        PointsLog.objects.filter(delta__lt=0).aggregate(total=models.Sum("delta"))[
            "total"
        ]
        or 0
    )

    avg_surveys_per_user = total_surveys / total_users if total_users > 0 else 0

    completed_surveys = Survey.objects.filter(status__in=["ended", "closed"]).count()
    survey_completion_rate = (
        completed_surveys / total_surveys * 100 if total_surveys > 0 else 0
    )

    return JsonResponse(
        {
            "total_users": total_users,
            "today_new_users": today_new_users,
            "active_users_7d": active_users_7d,
            "total_surveys": total_surveys,
            "published_surveys": published_surveys,
            "today_new_surveys": today_new_surveys,
            "total_fills": total_fills,
            "today_fills": today_fills,
            "avg_surveys_per_user": round(avg_surveys_per_user, 2),
            "completed_surveys": completed_surveys,
            "survey_completion_rate": round(survey_completion_rate, 2),
            "total_points_issued": total_points_issued,
            "total_points_consumed": abs(total_points_consumed),
        }
    )


@csrf_exempt
def dashboard_trend(request):
    user, err = require_admin(request)
    if err:
        return err

    days = parse_int(request.GET.get("days", 7))
    days = min(days, 90)

    today = timezone.now().date()
    result = []

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day, datetime.max.time()))

        new_users = AppUser.objects.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()

        new_surveys = Survey.objects.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()

        new_fills = Response.objects.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()

        result.append(
            {
                "date": day.isoformat(),
                "new_users": new_users,
                "new_surveys": new_surveys,
                "new_fills": new_fills,
            }
        )

    return JsonResponse({"trend": result})


@csrf_exempt
def export_dashboard(request):
    user, err = require_admin(request)
    if err:
        return err

    days = parse_int(request.GET.get("days", 7))
    days = min(days, 90)

    today = timezone.now().date()
    trend_data = []

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day, datetime.max.time()))

        new_users = AppUser.objects.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()

        new_surveys = Survey.objects.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()

        new_fills = Response.objects.filter(
            created_at__gte=day_start, created_at__lte=day_end
        ).count()

        trend_data.append(
            {
                "date": day.isoformat(),
                "new_users": new_users,
                "new_surveys": new_surveys,
                "new_fills": new_fills,
            }
        )

    return JsonResponse({"trend": trend_data, "days": days})


@csrf_exempt
def user_list(request):
    user, err = require_admin(request)
    if err:
        return err

    page = parse_int(request.GET.get("page", 1))
    page_size = parse_int(request.GET.get("page_size", 20))
    search = request.GET.get("search", "")
    profile_min = request.GET.get("profile_completion_min", "")
    profile_max = request.GET.get("profile_completion_max", "")

    queryset = AppUser.objects.all().order_by("-created_at")

    if search:
        queryset = queryset.filter(nickname__icontains=search) | queryset.filter(
            email__icontains=search
        )

    if profile_min:
        queryset = queryset.filter(profile_completion_rate__gte=float(profile_min))
    if profile_max:
        queryset = queryset.filter(profile_completion_rate__lte=float(profile_max))

    total = queryset.count()
    offset = (page - 1) * page_size
    users = queryset[offset : offset + page_size]

    result = []
    for u in users:
        is_admin = UserRole.objects.filter(user=u, role__name="admin").exists()
        level_info = LevelService.get_level_info(u)
        total_earned = (
            PointsLog.objects.filter(user=u, delta__gt=0).aggregate(
                total=models.Sum("delta")
            )["total"]
            or 0
        )
        total_consumed = (
            PointsLog.objects.filter(user=u, delta__lt=0).aggregate(
                total=models.Sum("delta")
            )["total"]
            or 0
        )
        surveys_published = Survey.objects.filter(owner=u).count()
        fills_count = Response.objects.filter(user=u).count()

        result.append(
            {
                "id": u.id,
                "nickname": u.nickname,
                "email": u.email,
                "created_at": u.created_at.isoformat(),
                "points": u.points,
                "activity_points": u.activity_points,
                "level": level_info["level"],
                "title": level_info["title"],
                "status": u.status,
                "is_admin": is_admin,
                "total_earned": total_earned,
                "total_consumed": abs(total_consumed),
                "surveys_published": surveys_published,
                "fills_count": fills_count,
                "last_active_at": (
                    u.last_active_at.isoformat() if u.last_active_at else None
                ),
                "profile_completion_rate": u.profile_completion_rate,
            }
        )

    return JsonResponse(
        {
            "users": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def export_users(request):
    user, err = require_admin(request)
    if err:
        return err

    users = AppUser.objects.all().order_by("-created_at")

    data = []
    for u in users:
        level_info = LevelService.get_level_info(u)
        data.append(
            {
                "ID": u.id,
                "昵称": u.nickname,
                "邮箱": u.email,
                "等级": level_info["level"],
                "称号": level_info["title"],
                "积分": u.points,
                "活跃度": u.activity_points,
                "状态": u.status,
                "注册时间": u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return JsonResponse({"success": True, "data": data, "total": len(data)})


@csrf_exempt
def survey_list(request):
    user, err = require_admin(request)
    if err:
        return err

    page = parse_int(request.GET.get("page", 1))
    page_size = parse_int(request.GET.get("page_size", 20))
    status = request.GET.get("status", "")
    search = request.GET.get("search", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    queryset = Survey.objects.all().order_by("-created_at")

    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(title__icontains=search)
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date + " 23:59:59")

    total = queryset.count()
    offset = (page - 1) * page_size
    surveys = queryset[offset : offset + page_size]

    result = []
    for s in surveys:
        survey_id = s.id

        impressions = RecommendationClaim.objects.filter(survey_id=survey_id).count()
        claimed_count = RecommendationClaim.objects.filter(survey_id=survey_id, status="completed").count()
        responses = Response.objects.filter(survey_id=survey_id, status="submitted")
        completed_count = responses.count()
        avg_duration = responses.aggregate(avg_dur=models.Avg("duration_seconds"))["avg_dur"] or 0
        risk_count = responses.filter(risk_flag=True).count()

        ctr = (claimed_count / impressions * 100) if impressions > 0 else 0
        completion_rate = (completed_count / impressions * 100) if impressions > 0 else 0
        risk_rate = (risk_count / completed_count * 100) if completed_count > 0 else 0

        result.append(
            {
                "id": s.id,
                "title": s.title,
                "owner_nickname": s.owner.nickname,
                "owner_id": s.owner.id,
                "created_at": s.created_at.isoformat(),
                "status": s.status,
                "difficulty": s.difficulty,
                "estimated_minutes": s.estimated_minutes,
                "target": s.target,
                "completed": s.completed,
                "reward_points": s.reward_points,
                "publish_cost_points": s.publish_cost_points,
                "impressions": impressions,
                "completed_count": completed_count,
                "ctr": round(ctr, 2),
                "completion_rate": round(completion_rate, 2),
                "avg_duration": round(avg_duration, 1),
                "risk_rate": round(risk_rate, 2),
            }
        )

    return JsonResponse(
        {
            "surveys": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def export_surveys(request):
    user, err = require_admin(request)
    if err:
        return err

    surveys = Survey.objects.all().order_by("-created_at")

    data = []
    for s in surveys:
        data.append(
            {
                "ID": s.id,
                "标题": s.title,
                "发布者": s.owner.nickname,
                "状态": s.status,
                "难度": s.difficulty or "-",
                "预计时间": f"{s.estimated_minutes or 0}分钟",
                "目标回收": s.target or "-",
                "已完成": s.completed or 0,
                "奖励积分": s.reward_points or 0,
                "创建时间": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return JsonResponse({"success": True, "data": data, "total": len(data)})


@csrf_exempt
def analytics_recommend(request):
    user, err = require_admin(request)
    if err:
        return err

    days = parse_int(request.GET.get("days", 7)) or 7
    days = min(max(days, 1), 90)
    start_dt = timezone.now() - timedelta(days=days)

    queryset = UserBehaviorLog.objects.filter(created_at__gte=start_dt)
    impressions = queryset.filter(event_type="impression").count()
    clicks = queryset.filter(event_type="click").count()
    refresh_count = queryset.filter(event_type="refresh").count()
    delete_count = queryset.filter(event_type="dismiss").count()
    ctr = (clicks / impressions * 100) if impressions > 0 else 0

    claimed_count = RecommendationClaim.objects.filter(
        claimed_at__gte=start_dt
    ).count()

    completed_count = RecommendationClaim.objects.filter(
        claimed_at__gte=start_dt,
        status="completed"
    ).count()

    claim_rate = (claimed_count / impressions * 100) if impressions > 0 else 0
    completion_rate = (completed_count / claimed_count * 100) if claimed_count > 0 else 0

    return JsonResponse(
        {
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 2),
            "refresh_count": refresh_count,
            "delete_count": delete_count,
            "claim_count": claimed_count,
            "completed_count": completed_count,
            "claim_rate": round(claim_rate, 2),
            "completion_rate": round(completion_rate, 2),
        }
    )


@csrf_exempt
def analytics_recommend_events(request):
    user, err = require_admin(request)
    if err:
        return err

    days = parse_int(request.GET.get("days", 7)) or 7
    days = min(max(days, 1), 90)
    page = parse_int(request.GET.get("page", 1)) or 1
    page_size = parse_int(request.GET.get("page_size", 20)) or 20
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    event_type = (request.GET.get("event_type") or "").strip()
    scene = (request.GET.get("scene") or "").strip()

    start_dt = timezone.now() - timedelta(days=days)
    period_queryset = UserBehaviorLog.objects.filter(created_at__gte=start_dt)
    queryset = period_queryset.select_related("user", "survey").order_by("-created_at")

    if event_type and event_type != "all":
        queryset = queryset.filter(event_type=event_type)
    if scene and scene != "all":
        queryset = queryset.filter(scene=scene)

    total = queryset.count()
    offset = (page - 1) * page_size
    events = queryset[offset : offset + page_size]

    items = []
    for event in events:
        items.append(
            {
                "id": event.id,
                "event_type": event.event_type,
                "scene": event.scene,
                "user_id": event.user_id,
                "user_nickname": event.user.nickname if event.user else None,
                "survey_id": event.survey_id,
                "survey_title": event.survey.title if event.survey else None,
                "meta": event.meta_json or {},
                "created_at": event.created_at.isoformat(),
            }
        )

    summary = {
        "impression": period_queryset.filter(event_type="impression").count(),
        "click": period_queryset.filter(event_type="click").count(),
        "refresh": period_queryset.filter(event_type="refresh").count(),
        "dismiss": period_queryset.filter(event_type="dismiss").count(),
    }

    return JsonResponse(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": summary,
        }
    )


@csrf_exempt
def analytics_ai(request):
    user, err = require_admin(request)
    if err:
        return err

    days = parse_int(request.GET.get("days", 7))
    days = min(days, 90)

    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))

    total_surveys = Survey.objects.filter(created_at__gte=start_dt).count()

    ai_surveys = Survey.objects.filter(
        created_at__gte=start_dt, ai_generated=True
    ).count()

    ai_rate = (ai_surveys / total_surveys * 100) if total_surveys > 0 else 0

    difficulty_dist = {}
    for diff in range(1, 6):
        count = Survey.objects.filter(
            created_at__gte=start_dt,
            difficulty=diff,
        ).count()
        difficulty_dist[diff] = count

    return JsonResponse(
        {
            "ai_surveys": ai_surveys,
            "total_surveys": total_surveys,
            "ai_rate": round(ai_rate, 2),
            "difficulty_distribution": difficulty_dist,
        }
    )


@csrf_exempt
def risk_control(request):
    user, err = require_admin(request)
    if err:
        return err

    from core.models import RiskEvent

    # 使用RiskEvent模型统计风控事件
    short_duration_count = RiskEvent.objects.filter(event_type="short_duration").count()
    suspicious_users = (
        RiskEvent.objects.filter(event_type="suspicious_behavior")
        .values("user")
        .distinct()
        .count()
    )
    abnormal_surveys = (
        RiskEvent.objects.filter(event_type="abnormal_survey")
        .values("survey")
        .distinct()
        .count()
    )

    page = parse_int(request.GET.get("page", 1))
    page_size = parse_int(request.GET.get("page_size", 20))
    risk_type = request.GET.get("type", "short_duration")

    items = []
    total = 0

    if risk_type == "short_duration":
        queryset = (
            RiskEvent.objects.filter(event_type="short_duration")
            .select_related("user", "survey")
            .order_by("-created_at")
        )
        total = queryset.count()
        for event in queryset[(page - 1) * page_size : page * page_size]:
            items.append(
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "user_nickname": event.user.nickname if event.user else None,
                    "survey_id": event.survey_id,
                    "survey_title": event.survey.title if event.survey else None,
                    "duration_seconds": (
                        event.detail.get("duration_seconds") if event.detail else None
                    ),
                    "severity": event.severity,
                    "created_at": event.created_at.isoformat(),
                }
            )
    elif risk_type == "suspicious_users":
        queryset = (
            RiskEvent.objects.filter(event_type="suspicious_behavior")
            .select_related("user")
            .order_by("-created_at")
        )
        total = queryset.count()
        for event in queryset[(page - 1) * page_size : page * page_size]:
            items.append(
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "user_nickname": event.user.nickname if event.user else None,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "detail": event.detail,
                    "created_at": event.created_at.isoformat(),
                }
            )
    elif risk_type == "abnormal_surveys":
        queryset = (
            RiskEvent.objects.filter(event_type="abnormal_survey")
            .select_related("survey", "survey__owner")
            .order_by("-created_at")
        )
        total = queryset.count()
        for event in queryset[(page - 1) * page_size : page * page_size]:
            items.append(
                {
                    "id": event.id,
                    "survey_id": event.survey_id,
                    "survey_title": event.survey.title if event.survey else None,
                    "owner_id": event.survey.owner_id if event.survey else None,
                    "owner_nickname": (
                        event.survey.owner.nickname
                        if event.survey and event.survey.owner
                        else None
                    ),
                    "severity": event.severity,
                    "detail": event.detail,
                    "created_at": event.created_at.isoformat(),
                }
            )

    return JsonResponse(
        {
            "short_duration_count": short_duration_count,
            "suspicious_users": suspicious_users,
            "abnormal_surveys": abnormal_surveys,
            "type": risk_type,
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def user_detail(request, user_id):
    user, err = require_admin(request)
    if err:
        return err

    try:
        target = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return error(404, "用户不存在")

    level_info = LevelService.get_level_info(target)

    total_earned = (
        PointsLog.objects.filter(user=target, delta__gt=0).aggregate(
            total=models.Sum("delta")
        )["total"]
        or 0
    )
    total_consumed = (
        PointsLog.objects.filter(user=target, delta__lt=0).aggregate(
            total=models.Sum("delta")
        )["total"]
        or 0
    )

    surveys_published = Survey.objects.filter(owner=target)
    fills = Response.objects.filter(user=target)
    is_admin = UserRole.objects.filter(user=target, role__name="admin").exists()

    return JsonResponse(
        {
            "id": target.id,
            "nickname": target.nickname,
            "email": target.email,
            "created_at": target.created_at.isoformat(),
            "status": target.status,
            "is_admin": is_admin,
            "points": target.points,
            "activity_points": target.activity_points,
            "level": level_info["level"],
            "title": level_info["title"],
            "exp": level_info["exp"],
            "exp_in_level": level_info["exp_in_level"],
            "exp_to_next": level_info["exp_to_next"],
            "progress_pct": level_info["progress_pct"],
            "total_earned": total_earned,
            "total_consumed": abs(total_consumed),
            "surveys_published": surveys_published.count(),
            "fills_count": fills.count(),
            "profile_completion_rate": target.profile_completion_rate,
            "profile_last_updated_at": target.profile_last_updated_at.isoformat() if target.profile_last_updated_at else None,
            "recent_surveys": [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                }
                for s in surveys_published[:5]
            ],
        }
    )


@csrf_exempt
def update_user_info(request, user_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        target = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return error(404, "用户不存在")

    data = parse_json(request)

    if "nickname" in data:
        target.nickname = data["nickname"]
    if "email" in data:
        target.email = data["email"]
    if "points" in data:
        old_points = target.points
        new_points = max(0, int(data["points"]))
        target.points = new_points
        if old_points != new_points:
            PointsLog.objects.create(
                user=target,
                points_type="admin_adjust",
                delta=new_points - old_points,
                reason=f"管理员调整积分: {old_points} -> {new_points}",
            )
    if "status" in data:
        target.status = data["status"]

    target.save()

    AuditLog.objects.create(
        target_type="user",
        target_id=target.id,
        action="update_user",
        operator=user,
        note=f"更新用户信息",
    )

    return JsonResponse({"success": True, "message": "用户信息已更新"})


@csrf_exempt
def delete_user(request, user_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        target = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return error(404, "用户不存在")

    if target.id == user.id:
        return error(400, "不能删除自己")

    target_nickname = target.nickname
    target.delete()

    AuditLog.objects.create(
        target_type="user",
        target_id=user_id,
        action="delete_user",
        operator=user,
        note=f"删除用户: {target_nickname}",
    )

    return JsonResponse({"success": True, "message": "用户已删除"})


@csrf_exempt
def update_user_status(request, user_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        target = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return error(404, "用户不存在")

    data = parse_json(request)
    new_status = data.get("status", "normal")
    target.status = new_status
    target.save(update_fields=["status", "updated_at"])

    return JsonResponse({"success": True, "new_status": new_status})


@csrf_exempt
def promote_user_admin(request, user_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        target = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return error(404, "用户不存在")

    admin_role, _ = Role.objects.get_or_create(
        name="admin", defaults={"description": "系统管理员"}
    )

    _, created = UserRole.objects.get_or_create(user=target, role=admin_role)

    AuditLog.objects.create(
        target_type="user",
        target_id=target.id,
        action="promote_admin",
        operator=user,
        note=f"提权为管理员: {target.nickname}({target.email})",
    )

    if created:
        return JsonResponse({"success": True, "message": "用户已提升为管理员"})

    return JsonResponse({"success": True, "message": "该用户已是管理员"})


@csrf_exempt
def batch_update_user_status(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    data = parse_json(request)
    user_ids = data.get("user_ids", [])
    new_status = data.get("status", "normal")

    if not user_ids:
        return error(400, "用户ID列表不能为空")

    updated_count = AppUser.objects.filter(id__in=user_ids).update(
        status=new_status, updated_at=timezone.now()
    )

    return JsonResponse({"success": True, "updated_count": updated_count})


@csrf_exempt
def batch_adjust_points(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    data = parse_json(request)
    user_ids = data.get("user_ids", [])
    delta = data.get("delta", 0)
    reason = data.get("reason", "管理员批量调整")

    if not user_ids:
        return error(400, "用户ID列表不能为空")

    if delta == 0:
        return error(400, "积分调整值不能为0")

    updated_users = []
    insufficient_users = []
    
    for uid in user_ids:
        try:
            target_user = AppUser.objects.get(id=uid)
            old_points = target_user.points
            new_points = old_points + delta
            
            actual_delta = delta
            is_insufficient = False
            
            if new_points < 0:
                actual_delta = -old_points
                new_points = 0
                is_insufficient = True
            
            target_user.points = new_points
            target_user.save(update_fields=["points", "updated_at"])

            log_reason = reason
            if is_insufficient:
                log_reason = f"{reason}（积分不足，已全部扣除）"
            
            PointsLog.objects.create(
                user=target_user,
                points_type="admin_adjust",
                delta=actual_delta,
                reason=log_reason,
                ref_type="batch_adjust",
                ref_id=user.id,
            )

            user_info = {
                "id": target_user.id,
                "nickname": target_user.nickname,
                "old_points": old_points,
                "actual_delta": actual_delta,
                "new_points": new_points,
                "is_insufficient": is_insufficient,
            }

            updated_users.append(user_info)
            if is_insufficient:
                insufficient_users.append(user_info)

        except AppUser.DoesNotExist:
            continue

    return JsonResponse(
        {
            "success": True,
            "updated_count": len(updated_users),
            "insufficient_count": len(insufficient_users),
            "updated_users": updated_users,
            "insufficient_users": insufficient_users,
        }
    )


@csrf_exempt
def notification_list(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "GET":
        return error(405, "请求方法不允许")

    page = parse_int(request.GET.get("page", 1)) or 1
    page_size = parse_int(request.GET.get("page_size", 20)) or 20
    status = request.GET.get("status", "")

    queryset = Message.objects.filter(user=user).order_by("-created_at")
    if status == "unread":
        queryset = queryset.filter(status="unread")
    elif status == "read":
        queryset = queryset.filter(status="read")

    total = queryset.count()
    offset = (page - 1) * page_size
    messages = queryset[offset : offset + page_size]

    return JsonResponse(
        {
            "messages": [
                {
                    "id": m.id,
                    "title": m.title,
                    "content": m.content,
                    "type": m.type,
                    "message_type": m.message_type,
                    "status": m.status,
                    "sender": m.sender.nickname if m.sender else "系统",
                    "created_at": m.created_at.isoformat(),
                    "read_at": m.read_at.isoformat() if m.read_at else None,
                }
                for m in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def notification_mark_read(request, message_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        message = Message.objects.get(id=message_id, user=user)
    except Message.DoesNotExist:
        return error(404, "通知不存在")

    message.status = "read"
    message.read_at = timezone.now()
    message.save(update_fields=["status", "read_at"])

    return JsonResponse({"success": True})


@csrf_exempt
def notification_mark_all_read(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    updated = Message.objects.filter(user=user, status="unread").update(
        status="read", read_at=timezone.now()
    )

    return JsonResponse({"success": True, "updated_count": updated})


@csrf_exempt
def create_announcement(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    data = parse_json(request)

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        return error(400, "标题和内容不能为空")

    target_type = data.get("target_type", "all")
    target_users = []

    if target_type == "all":
        target_users = AppUser.objects.all()
    elif target_type == "active":
        target_users = AppUser.objects.filter(status="normal")
    elif target_type == "inactive":
        target_users = AppUser.objects.exclude(status="normal")

    messages = []
    for target in target_users:
        messages.append(
            Message(
                user=target,
                sender=user,
                title=title,
                content=content,
                type="announcement",
                message_type="system",
                status="unread",
            )
        )

    Message.objects.bulk_create(messages)

    return JsonResponse(
        {"success": True, "message": f"公告已发送给 {len(messages)} 位用户"}
    )


@csrf_exempt
def announcement_list(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "GET":
        return error(405, "请求方法不允许")

    page = parse_int(request.GET.get("page", 1)) or 1
    page_size = parse_int(request.GET.get("page_size", 20)) or 20

    queryset = Message.objects.filter(sender=user, type="announcement").order_by(
        "-created_at"
    )

    total = queryset.count()
    offset = (page - 1) * page_size
    messages = queryset[offset : offset + page_size]

    return JsonResponse(
        {
            "messages": [
                {
                    "id": m.id,
                    "title": m.title,
                    "content": m.content,
                    "status": m.status,
                    "recipient": m.user.nickname,
                    "created_at": m.created_at.isoformat(),
                    "read_at": m.read_at.isoformat() if m.read_at else None,
                }
                for m in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def survey_detail(request, survey_id):
    user, err = require_admin(request)
    if err:
        return err

    try:
        survey = Survey.objects.select_related("owner").get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")
    except Exception as e:
        logger.exception("查询问卷失败")
        return internal_error(e)

    try:
        responses = Response.objects.filter(survey=survey)
        total_duration = sum(r.duration_seconds or 0 for r in responses)
        response_count = responses.count()
        avg_duration = total_duration / response_count if response_count > 0 else 0
    except Exception as e:
        logger.exception("查询响应数据失败")
        return internal_error(e)

    try:
        owner_nickname = survey.owner.nickname if survey.owner else "未知"
        owner_id = survey.owner.id if survey.owner else None
    except Exception as e:
        logger.exception("查询问卷所有者失败")
        owner_nickname = "未知"
        owner_id = None

    return JsonResponse(
        {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "owner_nickname": owner_nickname,
            "owner_id": owner_id,
            "created_at": survey.created_at.isoformat(),
            "status": survey.status,
            "difficulty": survey.difficulty,
            "estimated_minutes": survey.estimated_minutes,
            "target": survey.target,
            "completed": survey.completed,
            "reward_points": survey.reward_points,
            "publish_cost_points": survey.publish_cost_points,
            "ai_generated": survey.ai_generated,
            "response_count": response_count,
            "avg_duration_seconds": round(avg_duration, 2),
        }
    )


@csrf_exempt
def create_survey(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    data = parse_json(request)

    title = data.get("title", "").strip()
    if not title:
        return error(400, "问卷标题不能为空")

    survey = Survey.objects.create(
        title=title,
        description=data.get("description", ""),
        owner=user,
        difficulty=data.get("difficulty", ""),
        estimated_minutes=data.get("estimated_minutes", 0),
        target=data.get("target", 0),
        reward_points=data.get("reward_points", 0),
        publish_cost_points=data.get("publish_cost_points", 0),
        status="draft",
    )

    AuditLog.objects.create(
        target_type="survey",
        target_id=survey.id,
        action="create_survey",
        operator=user,
        note=f"创建问卷: {title}",
    )

    return JsonResponse({"success": True, "id": survey.id, "message": "问卷创建成功"})


@csrf_exempt
def update_survey(request, survey_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")

    data = parse_json(request)

    if "title" in data:
        survey.title = data["title"]
    if "description" in data:
        survey.description = data["description"]
    if "difficulty" in data:
        survey.difficulty = data["difficulty"]
    if "estimated_minutes" in data:
        survey.estimated_minutes = data["estimated_minutes"]
    if "target" in data:
        survey.target = data["target"]
    if "reward_points" in data:
        survey.reward_points = data["reward_points"]
    if "status" in data:
        survey.status = data["status"]

    survey.save()

    return JsonResponse({"success": True, "message": "问卷已更新"})


@csrf_exempt
def delete_survey(request, survey_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")

    survey_title = survey.title
    survey.delete()

    AuditLog.objects.create(
        target_type="survey",
        target_id=survey_id,
        action="delete_survey",
        operator=user,
        note=f"删除问卷: {survey_title}",
    )

    return JsonResponse({"success": True, "message": "问卷已删除"})


@csrf_exempt
def force_close_survey(request, survey_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")

    survey.status = "ended"
    survey.save()

    AuditLog.objects.create(
        target_type="survey",
        target_id=survey_id,
        action="force_close_survey",
        operator=user,
        note=f"强制关闭问卷: {survey.title}",
    )

    return JsonResponse({"success": True, "message": "问卷已强制结束"})


@csrf_exempt
def pending_surveys(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "GET":
        return error(405, "请求方法不允许")

    page = parse_int(request.GET.get("page", 1)) or 1
    page_size = parse_int(request.GET.get("page_size", 20)) or 20

    queryset = Survey.objects.filter(status="pending_review").order_by("-created_at")
    total = queryset.count()
    offset = (page - 1) * page_size
    surveys = queryset[offset : offset + page_size]

    return JsonResponse(
        {
            "surveys": [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "owner": s.owner.nickname,
                    "owner_id": s.owner.id,
                    "reward_points": s.reward_points,
                    "difficulty": s.difficulty,
                    "estimated_minutes": s.estimated_minutes,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                }
                for s in surveys
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def approve_survey(request, survey_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")

    if survey.status != "pending_review":
        return error(400, "该问卷不在待审核状态")

    survey.status = "published"
    survey.save()

    AuditLog.objects.create(
        target_type="survey",
        target_id=survey_id,
        action="approve_survey",
        operator=user,
        note=f"审核通过问卷: {survey.title}",
    )

    return JsonResponse({"success": True, "message": "问卷已审核通过"})


@csrf_exempt
def reject_survey(request, survey_id):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "POST":
        return error(405, "请求方法不允许")

    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")

    if survey.status != "pending_review":
        return error(400, "该问卷不在待审核状态")

    data = parse_json(request)
    reason = data.get("reason", "")

    survey.status = "rejected"
    survey.save()

    AuditLog.objects.create(
        target_type="survey",
        target_id=survey_id,
        action="reject_survey",
        operator=user,
        note=f"审核拒绝问卷: {survey.title}，原因: {reason}",
    )

    return JsonResponse({"success": True, "message": "问卷已审核拒绝"})


@csrf_exempt
def operation_logs(request):
    user, err = require_admin(request)
    if err:
        return err

    if request.method != "GET":
        return error(405, "请求方法不允许")

    page = parse_int(request.GET.get("page", 1)) or 1
    page_size = parse_int(request.GET.get("page_size", 20)) or 20
    action = request.GET.get("action", "")
    target_type = request.GET.get("target_type", "")

    queryset = AuditLog.objects.select_related("operator").all().order_by("-created_at")

    if action:
        queryset = queryset.filter(action__icontains=action)
    if target_type:
        queryset = queryset.filter(target_type=target_type)

    total = queryset.count()
    offset = (page - 1) * page_size
    logs = queryset[offset : offset + page_size]

    return JsonResponse(
        {
            "logs": [
                {
                    "id": log.id,
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "note": log.note,
                    "operator": log.operator.nickname if log.operator else "系统",
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@csrf_exempt
def risk_rules(request):
    user, err = require_admin(request)
    if err:
        return err

    from core.models import RiskRule

    if request.method == "GET":
        queryset = RiskRule.objects.all().order_by("priority")
        rules = []
        for rule in queryset:
            rules.append({
                "id": rule.id,
                "rule_code": rule.rule_code,
                "rule_name": rule.rule_name,
                "description": rule.description,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "event_type": rule.event_type,
                "severity": rule.severity,
                "conditions": rule.conditions,
                "actions": rule.actions,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat(),
            })
        return JsonResponse({"rules": rules})

    elif request.method == "POST":
        data = parse_json(request)
        try:
            rule = RiskRule.objects.create(
                rule_code=data["rule_code"],
                rule_name=data["rule_name"],
                description=data.get("description", ""),
                enabled=data.get("enabled", True),
                priority=data.get("priority", 100),
                event_type=data["event_type"],
                severity=data.get("severity", "medium"),
                conditions=data.get("conditions", {}),
                actions=data.get("actions", []),
            )
            AuditLog.objects.create(
                target_type="risk_rule",
                target_id=rule.id,
                action="create_risk_rule",
                operator=user,
                note=f"创建风控规则: {rule.rule_name}"
            )
            return JsonResponse({"success": True, "rule_id": rule.id})
        except Exception as e:
            return error(400, f"创建规则失败: {str(e)}")


@csrf_exempt
def risk_rule_detail(request, rule_id):
    user, err = require_admin(request)
    if err:
        return err

    from core.models import RiskRule

    try:
        rule = RiskRule.objects.get(id=rule_id)
    except RiskRule.DoesNotExist:
        return error(404, "规则不存在")

    if request.method == "GET":
        return JsonResponse({
            "id": rule.id,
            "rule_code": rule.rule_code,
            "rule_name": rule.rule_name,
            "description": rule.description,
            "enabled": rule.enabled,
            "priority": rule.priority,
            "event_type": rule.event_type,
            "severity": rule.severity,
            "conditions": rule.conditions,
            "actions": rule.actions,
            "created_at": rule.created_at.isoformat(),
            "updated_at": rule.updated_at.isoformat(),
        })

    elif request.method == "PUT":
        data = parse_json(request)
        if "rule_name" in data:
            rule.rule_name = data["rule_name"]
        if "description" in data:
            rule.description = data["description"]
        if "enabled" in data:
            rule.enabled = data["enabled"]
        if "priority" in data:
            rule.priority = data["priority"]
        if "event_type" in data:
            rule.event_type = data["event_type"]
        if "severity" in data:
            rule.severity = data["severity"]
        if "conditions" in data:
            rule.conditions = data["conditions"]
        if "actions" in data:
            rule.actions = data["actions"]
        rule.save()

        AuditLog.objects.create(
            target_type="risk_rule",
            target_id=rule.id,
            action="update_risk_rule",
            operator=user,
            note=f"更新风控规则: {rule.rule_name}"
        )
        return JsonResponse({"success": True})

    elif request.method == "DELETE":
        rule_name = rule.rule_name
        rule.delete()
        AuditLog.objects.create(
            target_type="risk_rule",
            target_id=rule_id,
            action="delete_risk_rule",
            operator=user,
            note=f"删除风控规则: {rule_name}"
        )
        return JsonResponse({"success": True})


@csrf_exempt
def risk_rule_toggle(request, rule_id):
    user, err = require_admin(request)
    if err:
        return err

    from core.models import RiskRule

    try:
        rule = RiskRule.objects.get(id=rule_id)
    except RiskRule.DoesNotExist:
        return error(404, "规则不存在")

    rule.enabled = not rule.enabled
    rule.save()

    AuditLog.objects.create(
        target_type="risk_rule",
        target_id=rule.id,
        action="toggle_risk_rule",
        operator=user,
        note=f"{'启用' if rule.enabled else '禁用'}风控规则: {rule.rule_name}"
    )
    return JsonResponse({"success": True, "enabled": rule.enabled})
