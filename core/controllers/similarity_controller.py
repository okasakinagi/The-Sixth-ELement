import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.services.similarity_service import SimilarityService
from core.managers.similarity_manager import SimilarityManager
from core.views import error, require_auth
from core.views import (
    parse_int_id,
    WEIGHT_DISMISS_DECREMENT,
    WEIGHT_ABANDON_DECREMENT,
    WEIGHT_MIN,
    WEIGHT_MAX,
)
from core.models import UserTagWeight, SurveyTag, Response


def parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@csrf_exempt
def compute_user_survey_cosine(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    user_id = data.get("user_id")
    survey_id = data.get("survey_id")
    if not user_id or not survey_id:
        return error(422, "user_id and survey_id required")
    payload = SimilarityService.get_or_compute_daily_cosine(user_id, survey_id)
    if payload.get("error"):
        return error(422, payload.get("message"))
    return JsonResponse({"cosine": payload["cosine"], "cached": payload["cached"]})


@csrf_exempt
def encode_text_to_vector(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    ref_type = data.get("ref_type")
    ref_id = data.get("ref_id")
    text = data.get("text", "")
    dim = int(data.get("dim", 100) or 100)
    if not ref_type or not ref_id or not text:
        return error(422, "ref_type, ref_id and text required")
    # only allow ref_type in ('user','survey')
    if ref_type not in ("user", "survey"):
        return error(422, "ref_type must be 'user' or 'survey'")
    vec = SimilarityService.encode_and_store(ref_type, ref_id, text, dim=dim)
    return JsonResponse({"vector": vec})


@csrf_exempt
def generate_placeholder_string(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    ref_type = data.get("ref_type")
    ref_id = data.get("ref_id")
    if not ref_type or not ref_id:
        return error(422, "ref_type and ref_id required")
    if ref_type not in ("user", "survey"):
        return error(422, "ref_type must be 'user' or 'survey'")
    s = SimilarityService.generate_placeholder(ref_type, ref_id)
    return JsonResponse({"text": s})


@csrf_exempt
def generate_and_store_vector(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    ref_type = data.get("ref_type")
    ref_id = data.get("ref_id")
    dim = int(data.get("dim", 100) or 100)
    if not ref_type or not ref_id:
        return error(422, "ref_type and ref_id required")
    if ref_type not in ("user", "survey"):
        return error(422, "ref_type must be 'user' or 'survey'")
    vec = SimilarityService.generate_and_store_vector(ref_type, ref_id, dim=dim)
    return JsonResponse({"vector": vec})


@csrf_exempt
def dismiss_survey(request):
    """用户在任务大厅点击不感兴趣/删除时调用，减少相关 tag 权重。"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = json.loads(request.body.decode("utf-8")) if request.body else {}
    survey_id = data.get("survey_id")
    if not survey_id:
        return error(422, "survey_id required")
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    # 获取 survey 的 tags 并减少权重
    try:
        tags = SurveyTag.objects.filter(survey_id=survey_pk).select_related("tag")
        for st in tags:
            tag = st.tag
            utw, _ = UserTagWeight.objects.get_or_create(user=user, tag=tag)
            new_w = utw.weight + WEIGHT_DISMISS_DECREMENT
            if new_w < WEIGHT_MIN:
                new_w = WEIGHT_MIN
            utw.weight = new_w
            utw.save(update_fields=["weight", "updated_at"])
    except Exception:
        return JsonResponse({"error": "failed to update weights"}, status=500)
    # 权重更新后使用户向量失效，下次推荐时重新生成
    try:
        SimilarityManager.invalidate_vector("user", str(user.id))
    except Exception:
        pass
    return JsonResponse({"status": "ok"})


@csrf_exempt
def abandon_fill(request, fill_id):
    """用户在填写界面点击返回/放弃时调用，减少相关 tag 权重（减少为 DISMISS 的五分之一）。"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    response_pk = parse_int_id(fill_id)
    if response_pk is None:
        return error(422, "invalid fill id")
    try:
        record = Response.objects.select_related("survey").get(
            id=response_pk, user=user
        )
    except Response.DoesNotExist:
        return error(404, "fill record not found")
    # 对该问卷的 tags 减少小幅权重
    try:
        tags = SurveyTag.objects.filter(survey_id=record.survey_id).select_related(
            "tag"
        )
        for st in tags:
            tag = st.tag
            utw, _ = UserTagWeight.objects.get_or_create(user=user, tag=tag)
            new_w = utw.weight + WEIGHT_ABANDON_DECREMENT
            if new_w < WEIGHT_MIN:
                new_w = WEIGHT_MIN
            utw.weight = new_w
            utw.save(update_fields=["weight", "updated_at"])
    except Exception:
        return JsonResponse({"error": "failed to update weights"}, status=500)
    # 权重更新后使用户向量失效，下次推荐时重新生成
    try:
        SimilarityManager.invalidate_vector("user", str(user.id))
    except Exception:
        pass
    return JsonResponse({"status": "ok"})


@csrf_exempt
def abandon_by_survey(request):
    """当用户在填写界面放弃但未创建 fill record 时，前端可以调用此接口传入 survey_id。"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    survey_id = data.get("survey_id")
    if not survey_id:
        return error(422, "survey_id required")
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    try:
        tags = SurveyTag.objects.filter(survey_id=survey_pk).select_related("tag")
        for st in tags:
            tag = st.tag
            utw, _ = UserTagWeight.objects.get_or_create(user=user, tag=tag)
            new_w = utw.weight + WEIGHT_ABANDON_DECREMENT
            if new_w < WEIGHT_MIN:
                new_w = WEIGHT_MIN
            utw.weight = new_w
            utw.save(update_fields=["weight", "updated_at"])
    except Exception:
        return JsonResponse({"error": "failed to update weights"}, status=500)
    # 权重更新后使用户向量失效，下次推荐时重新生成
    try:
        SimilarityManager.invalidate_vector("user", str(user.id))
    except Exception:
        pass
    return JsonResponse({"status": "ok"})
