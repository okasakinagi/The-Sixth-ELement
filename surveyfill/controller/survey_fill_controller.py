"""
SurveyFill Controller - 控制器层
处理HTTP请求/响应、参数校验、调用Service层
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, parse_json, require_auth
from surveyfill.service.survey_fill_service import SurveyFillError, SurveyFillService


survey_fill_service = SurveyFillService()


@csrf_exempt
def survey_fill_detail(request, survey_id):
    if request.method != "GET":
        return error(405, "Method not allowed")
    try:
        payload = survey_fill_service.get_survey_fill(survey_id)
        return JsonResponse(payload, status=200)
    except SurveyFillError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
def submit_survey_fill(request, survey_id):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    try:
        payload = survey_fill_service.submit_survey_fill(survey_id, user, data)
        return JsonResponse(payload, status=200)
    except SurveyFillError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")
