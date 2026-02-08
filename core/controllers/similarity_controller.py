import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.services.similarity_service import SimilarityService
from core.views import error, require_auth


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
def recommend_surveys(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    user_id = data.get("user_id")
    num = int(data.get("num", 10) or 10)
    if not user_id:
        return error(422, "user_id required")
    payload = SimilarityService.recommend_surveys_for_user(user_id, num)
    return JsonResponse({"items": payload})
