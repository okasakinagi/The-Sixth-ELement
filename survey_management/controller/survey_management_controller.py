"""
Survey Management Controller - handles survey management endpoints.
"""

import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, require_auth, parse_deadline
from survey_management.service.survey_management_service import (
    SurveyManagementError,
    SurveyManagementService,
)


service = SurveyManagementService()


def _parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _parse_survey_id(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    match = re.search(r"\d+", raw)
    if not match:
        return None
    try:
        return int(match.group(0))
    except (TypeError, ValueError):
        return None


@csrf_exempt
def surveys_handler(request):
    user, err = require_auth(request)
    if err:
        return err

    if request.method == "GET":
        try:
            payload = service.list_surveys(
                user,
                {
                    "status": request.GET.get("status"),
                    "keyword": request.GET.get("keyword"),
                },
            )
            return JsonResponse(payload, status=200)
        except SurveyManagementError as exc:
            return error(exc.status, exc.message)
        except Exception as exc:
            return error(500, f"Internal server error: {str(exc)}")

    if request.method == "POST":
        data = _parse_json(request)
        if "deadline" in data:
            data["deadline"] = parse_deadline(data.get("deadline"))
        try:
            payload = service.create_survey(user, data)
            return JsonResponse(payload, status=200)
        except SurveyManagementError as exc:
            return error(exc.status, exc.message)
        except Exception as exc:
            return error(500, f"Internal server error: {str(exc)}")

    return error(405, "Method not allowed")


@csrf_exempt
def surveys_summary(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = service.get_summary(user)
        return JsonResponse(payload, status=200)
    except SurveyManagementError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def survey_detail_handler(request, survey_id):
    user, err = require_auth(request)
    if err:
        return err
    survey_pk = _parse_survey_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")

    if request.method == "GET":
        try:
            payload = service.get_detail(user, survey_pk)
            return JsonResponse(payload, status=200)
        except SurveyManagementError as exc:
            return error(exc.status, exc.message)
        except Exception as exc:
            return error(500, f"Internal server error: {str(exc)}")

    if request.method == "DELETE":
        try:
            payload = service.delete_survey(user, survey_pk)
            return JsonResponse(payload, status=200)
        except SurveyManagementError as exc:
            return error(exc.status, exc.message)
        except Exception as exc:
            return error(500, f"Internal server error: {str(exc)}")

    return error(405, "Method not allowed")


@csrf_exempt
def pause_survey(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    survey_pk = _parse_survey_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    try:
        payload = service.pause_survey(user, survey_pk)
        return JsonResponse(payload, status=200)
    except SurveyManagementError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def resume_survey(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    survey_pk = _parse_survey_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    try:
        payload = service.resume_survey(user, survey_pk)
        return JsonResponse(payload, status=200)
    except SurveyManagementError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def publish_survey(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    survey_pk = _parse_survey_id(survey_id)
    if survey_pk is None:
        return error(422, "invalid survey id")
    data = _parse_json(request)
    try:
        payload = service.publish_survey(user, survey_pk, data)
        return JsonResponse(payload, status=200)
    except SurveyManagementError as exc:
        if exc.status == 422:
            return JsonResponse(
                {"error": {"message": exc.message, "details": {}}}, status=exc.status
            )
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")
