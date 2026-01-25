import json
import secrets
from datetime import datetime, time, timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import (
    AppUser,
    AuthCredential,
    AuthToken,
    PointsLog,
    Questionnaire,
    Report,
    Response,
    Survey,
    Tag,
    UserTag,
)


def now_iso(dt=None):
    value = dt or timezone.now()
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def error(status, message):
    return JsonResponse({"error": message}, status=status)


def parse_int_id(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    if "_" in raw:
        raw = raw.split("_", 1)[1]
    if not raw.isdigit():
        return None
    return int(raw)


def issue_token(user):
    AuthToken.objects.filter(user=user).delete()
    token = secrets.token_urlsafe(24)
    expires_at = timezone.now() + timedelta(seconds=3600)
    AuthToken.objects.create(user=user, token=token, expires_at=expires_at)
    return token, expires_at


def parse_deadline(value):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None:
        date_value = parse_date(value)
        if date_value:
            dt = datetime.combine(date_value, time.min)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone=timezone.utc)
    return dt


def normalize_tags(value):
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = str(value).split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def set_user_tags(user, tag_type, tags):
    UserTag.objects.filter(user=user, tag__type=tag_type).delete()
    seen = set()
    for name in normalize_tags(tags):
        if name in seen:
            continue
        seen.add(name)
        tag, _ = Tag.objects.get_or_create(name=name, type=tag_type)
        UserTag.objects.create(user=user, tag=tag)


def get_current_user(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    auth_token = AuthToken.objects.select_related("user").filter(token=token).first()
    if not auth_token:
        return None
    if auth_token.expires_at and auth_token.expires_at <= timezone.now():
        return None
    return auth_token.user


def require_auth(request):
    user = get_current_user(request)
    if not user:
        return None, error(401, "Unauthorized")
    return user, None


def user_response(user):
    return {
        "id": str(user.id),
        "nickname": user.nickname,
        "credit_score": user.credit_score,
        "points": user.points,
        "activity_points": user.activity_points,
        "has_honor": user.credit_score >= 85,
    }


def survey_response(survey):
    return {
        "id": str(survey.id),
        "title": survey.title,
        "description": survey.description,
        "link": None,
        "reward_points": survey.reward_points,
        "estimated_minutes": survey.estimated_minutes,
        "deadline": now_iso(survey.deadline) if survey.deadline else None,
        "status": survey.status,
        "created_at": now_iso(survey.created_at),
        "owner_id": str(survey.owner_id),
    }


def index(request):
    return HttpResponse(
        "Frontend is served by Vite. Start it from frontend/sixth_element.",
        content_type="text/plain; charset=utf-8",
    )


@csrf_exempt
def register(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    data = parse_json(request)
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()
    if not email or not password or not nickname:
        return error(422, "email, password, nickname required")
    if AppUser.objects.filter(email=email).exists():
        return error(422, "email already registered")

    user = AppUser.objects.create(
        email=email,
        nickname=nickname,
        credit_score=80,
        points=20,
        activity_points=0,
        status="normal",
    )
    AuthCredential.objects.create(user=user, password_hash=make_password(password))
    token, _ = issue_token(user)
    return JsonResponse(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": str(user.id), "nickname": user.nickname},
        }
    )


@csrf_exempt
def login(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    data = parse_json(request)
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if not email or not password:
        return error(422, "email and password required")

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return error(401, "invalid credentials")

    credential = AuthCredential.objects.filter(user=user).first()
    if not credential or not check_password(password, credential.password_hash):
        return error(401, "invalid credentials")

    token, _ = issue_token(user)
    return JsonResponse(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": str(user.id), "nickname": user.nickname},
        }
    )


@csrf_exempt
def user_me(request):
    user, err = require_auth(request)
    if err:
        return err
    if request.method == "GET":
        return JsonResponse(user_response(user))
    if request.method != "PATCH":
        return error(405, "Method not allowed")
    data = parse_json(request)
    nickname = data.get("nickname", user.nickname)
    school = data.get("school", None)
    tags = data.get("tags", None)
    user.nickname = nickname
    user.save(update_fields=["nickname"])
    if school is not None:
        set_user_tags(user, "school", [school] if school else [])
    if tags is not None:
        set_user_tags(user, "interest", tags)
    return JsonResponse(user_response(user))


@csrf_exempt
def surveys(request):
    if request.method == "POST":
        user, err = require_auth(request)
        if err:
            return err
        data = parse_json(request)
        title = data.get("title", "").strip()
        reward_points = int(data.get("reward_points", 0) or 0)
        if not title:
            return error(422, "title required")
        if reward_points < 0:
            return error(422, "reward_points must be >= 0")
        if user.points < reward_points:
            return error(422, "not enough points to publish survey")

        survey = Survey.objects.create(
            owner=user,
            title=title,
            description=data.get("description"),
            reward_points=reward_points,
            publish_cost_points=reward_points,
            deadline=parse_deadline(data.get("deadline")),
            estimated_minutes=data.get("estimated_minutes"),
            status="published",
        )
        questionnaire = Questionnaire.objects.create(
            survey=survey,
            version=1,
            status="published",
            title=title,
        )
        survey.active_questionnaire = questionnaire
        survey.save(update_fields=["active_questionnaire"])
        if reward_points > 0:
            user.points -= reward_points
            user.save(update_fields=["points"])
            PointsLog.objects.create(
                user=user,
                points_type="publish_cost",
                delta=-reward_points,
                reason="发布问卷消耗",
            )
        return JsonResponse({"id": str(survey.id), "status": "active"})

    if request.method != "GET":
        return error(405, "Method not allowed")

    status = request.GET.get("status")
    min_points = request.GET.get("min_points")
    max_minutes = request.GET.get("max_minutes")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    queryset = Survey.objects.all().order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    if min_points:
        queryset = queryset.filter(reward_points__gte=int(min_points))
    if max_minutes:
        queryset = queryset.filter(estimated_minutes__lte=int(max_minutes))

    total = queryset.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": str(survey.id),
            "title": survey.title,
            "reward_points": survey.reward_points,
            "estimated_minutes": survey.estimated_minutes,
            "deadline": now_iso(survey.deadline) if survey.deadline else None,
        }
        for survey in queryset[offset : offset + page_size]
    ]
    return JsonResponse(
        {"items": items, "page": page, "page_size": page_size, "total": total}
    )


def survey_detail(request, survey_id):
    if request.method != "GET":
        return error(405, "Method not allowed")
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    try:
        survey = Survey.objects.get(id=survey_pk)
    except Survey.DoesNotExist:
        return error(404, "survey not found")
    return JsonResponse(survey_response(survey))


@csrf_exempt
def close_survey(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    try:
        survey = Survey.objects.get(id=survey_pk)
    except Survey.DoesNotExist:
        return error(404, "survey not found")
    if survey.owner_id != user.id:
        return error(403, "not survey owner")
    survey.status = "closed"
    survey.save(update_fields=["status"])
    return JsonResponse({"id": str(survey.id), "status": "closed"})


@csrf_exempt
def submit_fill(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    duration = data.get("duration_seconds")
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    try:
        survey = Survey.objects.get(id=survey_pk)
    except Survey.DoesNotExist:
        return error(404, "survey not found")
    if survey.status != "published":
        return error(422, "survey not published")
    if survey.owner_id == user.id:
        return error(422, "cannot fill your own survey")
    if Response.objects.filter(survey=survey, user=user).exists():
        return error(422, "already filled")

    response = Response.objects.create(
        survey=survey,
        questionnaire=survey.active_questionnaire,
        user=user,
        duration_seconds=duration,
        status="submitted",
        submitted_at=timezone.now(),
    )
    return JsonResponse(
        {"id": str(response.id), "status": response.status, "points_awarded": 0}
    )


@csrf_exempt
def review_fill(request, fill_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    status = data.get("status")
    if status not in ("approved", "rejected"):
        return error(422, "status must be approved or rejected")
    response_pk = parse_int_id(fill_id)
    if response_pk is None:
        return error(422, "invalid fill id")

    try:
        record = Response.objects.select_related("survey", "user").get(id=response_pk)
    except Response.DoesNotExist:
        return error(404, "fill record not found")
    if record.survey.owner_id != user.id:
        return error(403, "not survey owner")
    if record.status != "submitted":
        return error(422, "record already reviewed")

    points_awarded = 0
    if status == "approved":
        points_awarded = record.survey.reward_points
        record.user.points += points_awarded
        record.user.activity_points += points_awarded
        record.user.save(update_fields=["points", "activity_points"])
        PointsLog.objects.create(
            user=record.user,
            points_type="reward",
            delta=points_awarded,
            reason="完成问卷",
        )

    record.status = status
    record.save(update_fields=["status"])
    return JsonResponse(
        {"id": str(record.id), "status": status, "points_awarded": points_awarded}
    )


def my_fills(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    status = request.GET.get("status")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    queryset = Response.objects.filter(user=user).order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    total = queryset.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": str(record.id),
            "survey_id": str(record.survey_id),
            "status": record.status,
            "created_at": now_iso(record.created_at),
        }
        for record in queryset[offset : offset + page_size]
    ]
    return JsonResponse(
        {"items": items, "page": page, "page_size": page_size, "total": total}
    )


def points_logs(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    log_type = request.GET.get("type")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    queryset = PointsLog.objects.filter(user=user).order_by("-created_at")
    if log_type == "earn":
        queryset = queryset.filter(points_type__in=["reward", "admin_adjust"])
    elif log_type == "spend":
        queryset = queryset.filter(points_type__in=["publish_cost", "admin_adjust"])
    
    total = queryset.count()
    offset = (page - 1) * page_size
    items = []
    
    for log in queryset[offset : offset + page_size]:
        # Try to find associated survey or fill record for navigation
        related_id = None
        related_type = None
        
        if "问卷" in log.reason or "填" in log.reason:
            # Try to find matching fill record by timestamp and delta
            try:
                if log.delta > 0:  # Earn - likely from completing a survey
                    fill = Response.objects.filter(
                        user=user, 
                        created_at__date=log.created_at.date()
                    ).first()
                    if fill:
                        related_id = str(fill.survey_id)
                        related_type = "survey_fill"
                elif log.delta < 0:  # Spend - likely from publishing
                    survey = Survey.objects.filter(
                        owner=user,
                        reward_points=-log.delta,
                        created_at__date=log.created_at.date()
                    ).first()
                    if survey:
                        related_id = str(survey.id)
                        related_type = "survey_publish"
            except:
                pass
        
        items.append({
            "id": str(log.id),
            "delta": log.delta,
            "reason": log.reason,
            "created_at": now_iso(log.created_at),
            "related_id": related_id,
            "related_type": related_type,
        })
    
    # Calculate honor status: credit_score >= 85 = qualified
    has_honor = user.credit_score >= 85
    
    return JsonResponse(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "user": {
                "id": str(user.id),
                "points": user.points,
                "credit_score": user.credit_score,
                "activity_points": user.activity_points,
                "has_honor": has_honor,
            },
        }
    )


@csrf_exempt
def create_report(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    target_type = data.get("target_type", "").strip()
    target_id_raw = data.get("target_id", "")
    reason = data.get("reason", "").strip()
    if not target_type or not target_id_raw or not reason:
        return error(422, "target_type, target_id, reason required")

    target_id = parse_int_id(target_id_raw)
    if target_id is None:
        return error(422, "invalid target_id")
    if target_type == "survey":
        if not Survey.objects.filter(id=target_id).exists():
            return error(404, "survey not found")
    elif target_type == "user":
        if not AppUser.objects.filter(id=target_id).exists():
            return error(404, "user not found")
    else:
        return error(422, "target_type must be survey or user")

    report = Report.objects.create(
        reporter=user,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        status="open",
    )
    return JsonResponse({"id": str(report.id), "status": report.status})
