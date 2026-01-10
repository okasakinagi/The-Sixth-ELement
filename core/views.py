import json
import secrets
import uuid

from django.http import JsonResponse
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import AppUser, Survey, FillRecord, PointsLog, Report


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


def get_current_user(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        return AppUser.objects.get(token=token)
    except AppUser.DoesNotExist:
        return None


def require_auth(request):
    user = get_current_user(request)
    if not user:
        return None, error(401, "Unauthorized")
    return user, None


def user_response(user):
    return {
        "id": user.id,
        "nickname": user.nickname,
        "credit_score": user.credit_score,
        "points": user.points,
        "activity_points": user.activity_points,
    }


def survey_response(survey):
    return {
        "id": survey.id,
        "title": survey.title,
        "description": survey.description,
        "link": survey.link,
        "reward_points": survey.reward_points,
        "estimated_minutes": survey.estimated_minutes,
        "deadline": survey.deadline,
        "status": survey.status,
        "created_at": now_iso(survey.created_at),
        "owner_id": survey.owner_id,
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

    user_id = f"u_{uuid.uuid4().hex}"
    token = secrets.token_urlsafe(24)
    user = AppUser.objects.create(
        id=user_id,
        email=email,
        password=password,
        nickname=nickname,
        token=token,
    )
    return JsonResponse(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": user.id, "nickname": user.nickname},
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
        user = AppUser.objects.get(email=email, password=password)
    except AppUser.DoesNotExist:
        return error(401, "invalid credentials")

    token = secrets.token_urlsafe(24)
    user.token = token
    user.save(update_fields=["token"])
    return JsonResponse(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": user.id, "nickname": user.nickname},
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
    school = data.get("school", user.school)
    tags = data.get("tags", user.tags)
    if isinstance(tags, list):
        tags = ",".join([str(tag).strip() for tag in tags if str(tag).strip()])
    user.nickname = nickname
    user.school = school
    user.tags = tags
    user.save(update_fields=["nickname", "school", "tags"])
    return JsonResponse(user_response(user))


@csrf_exempt
def surveys(request):
    if request.method == "POST":
        user, err = require_auth(request)
        if err:
            return err
        data = parse_json(request)
        title = data.get("title", "").strip()
        link = data.get("link", "").strip()
        reward_points = int(data.get("reward_points", 0) or 0)
        if not title or not link:
            return error(422, "title and link required")
        if reward_points < 0:
            return error(422, "reward_points must be >= 0")
        if user.points < reward_points:
            return error(422, "not enough points to publish survey")

        survey_id = f"s_{uuid.uuid4().hex}"
        Survey.objects.create(
            id=survey_id,
            owner=user,
            title=title,
            description=data.get("description"),
            link=link,
            reward_points=reward_points,
            deadline=data.get("deadline"),
            estimated_minutes=data.get("estimated_minutes"),
            status="active",
        )
        if reward_points > 0:
            user.points -= reward_points
            user.save(update_fields=["points"])
            PointsLog.objects.create(
                id=f"p_{uuid.uuid4().hex}",
                user=user,
                delta=-reward_points,
                reason="发布问卷消耗",
            )
        return JsonResponse({"id": survey_id, "status": "active"})

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
            "id": survey.id,
            "title": survey.title,
            "reward_points": survey.reward_points,
            "estimated_minutes": survey.estimated_minutes,
            "deadline": survey.deadline,
        }
        for survey in queryset[offset : offset + page_size]
    ]
    return JsonResponse(
        {"items": items, "page": page, "page_size": page_size, "total": total}
    )


def survey_detail(request, survey_id):
    if request.method != "GET":
        return error(405, "Method not allowed")
    try:
        survey = Survey.objects.get(id=survey_id)
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
    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "survey not found")
    if survey.owner_id != user.id:
        return error(403, "not survey owner")
    survey.status = "closed"
    survey.save(update_fields=["status"])
    return JsonResponse({"id": survey_id, "status": "closed"})


@csrf_exempt
def submit_fill(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    duration = data.get("duration_seconds")
    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return error(404, "survey not found")
    if survey.status != "active":
        return error(422, "survey not active")
    if survey.owner_id == user.id:
        return error(422, "cannot fill your own survey")
    if FillRecord.objects.filter(survey=survey, user=user).exists():
        return error(422, "already filled")

    fill_id = f"f_{uuid.uuid4().hex}"
    FillRecord.objects.create(
        id=fill_id,
        survey=survey,
        user=user,
        duration_seconds=duration,
        status="pending",
        points_awarded=0,
    )
    return JsonResponse({"id": fill_id, "status": "pending", "points_awarded": 0})


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

    try:
        record = FillRecord.objects.select_related("survey", "user").get(id=fill_id)
    except FillRecord.DoesNotExist:
        return error(404, "fill record not found")
    if record.survey.owner_id != user.id:
        return error(403, "not survey owner")
    if record.status != "pending":
        return error(422, "record already reviewed")

    points_awarded = 0
    if status == "approved":
        points_awarded = record.survey.reward_points
        record.user.points += points_awarded
        record.user.activity_points += points_awarded
        record.user.save(update_fields=["points", "activity_points"])
        PointsLog.objects.create(
            id=f"p_{uuid.uuid4().hex}",
            user=record.user,
            delta=points_awarded,
            reason="完成问卷",
        )

    record.status = status
    record.points_awarded = points_awarded
    record.save(update_fields=["status", "points_awarded"])
    return JsonResponse(
        {"id": fill_id, "status": status, "points_awarded": points_awarded}
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

    queryset = FillRecord.objects.filter(user=user).order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    total = queryset.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": record.id,
            "survey_id": record.survey_id,
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
        queryset = queryset.filter(delta__gt=0)
    elif log_type == "spend":
        queryset = queryset.filter(delta__lt=0)
    total = queryset.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": log.id,
            "delta": log.delta,
            "reason": log.reason,
            "created_at": now_iso(log.created_at),
        }
        for log in queryset[offset : offset + page_size]
    ]
    return JsonResponse(
        {"items": items, "page": page, "page_size": page_size, "total": total}
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
    target_id = data.get("target_id", "").strip()
    reason = data.get("reason", "").strip()
    if not target_type or not target_id or not reason:
        return error(422, "target_type, target_id, reason required")

    report_id = f"r_{uuid.uuid4().hex}"
    Report.objects.create(
        id=report_id,
        reporter=user,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        status="pending",
    )
    return JsonResponse({"id": report_id, "status": "pending"})
