"""
SurveyFill Controller - 控制器层
处理HTTP请求/响应、参数校验、调用Service层
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, get_current_user, internal_error, parse_int_id, parse_json, require_auth
from core.services.user_behavior_log_service import UserBehaviorLogService
from surveyfill.service.survey_fill_service import SurveyFillError, SurveyFillService


survey_fill_service = SurveyFillService()


@csrf_exempt
def survey_fill_detail(request, survey_id):
    if request.method != "GET":
        return error(405, "Method not allowed")
    try:
        payload = survey_fill_service.get_survey_fill(survey_id)
        current_user = get_current_user(request)
        if current_user:
            survey_pk = parse_int_id(survey_id)
            if survey_pk is not None:
                UserBehaviorLogService.log_event(
                    user_id=current_user.id,
                    event_type="click",
                    survey_id=survey_pk,
                    scene="fill_entry",
                )
        return JsonResponse(payload, status=200)
    except SurveyFillError as e:
        return error(e.status, e.message)
    except Exception as e:
        return internal_error(e)


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
        return internal_error(e)
