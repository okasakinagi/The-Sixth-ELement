"""
UserProfile Controller - 控制器层
处理HTTP请求/响应、参数验证、调用Service层
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.views import parse_json, error, require_auth
from ..services.profile_service import UserProfileService


profile_service = UserProfileService()


@csrf_exempt
def user_profile_handler(request):
    """
    用户画像统一处理器 - 根据HTTP方法路由
    
    GET /users/me/profile - 获取画像
    PATCH /users/me/profile - 部分更新画像
    PUT /users/me/profile - 完整替换画像
    """
    if request.method == "GET":
        return get_user_profile(request)
    elif request.method == "PATCH":
        return update_user_profile(request)
    elif request.method == "PUT":
        return replace_user_profile(request)
    else:
        return error(405, "Method not allowed")


@csrf_exempt
def get_user_profile(request):
    """
    获取当前用户画像
    内部函数，由user_profile_handler调用
    """
    # 认证检查
    user, err = require_auth(request)
    if err:  # 认证失败
        return err
    
    try:
        # 调用Service获取画像
        profile_data = profile_service.get_profile(user)
        return JsonResponse(profile_data, status=200)
    
    except Exception as e:
        import traceback
        print("=" * 80)
        print("ERROR in get_user_profile:")
        print(traceback.format_exc())
        print("=" * 80)
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
def update_user_profile(request):
    """
    更新当前用户画像（部分更新）
    内部函数，由user_profile_handler调用
    """
    # 认证检查
    user, err = require_auth(request)
    if err:
        return err
    
    # 解析请求数据
    data = parse_json(request)
    if not data:
        return error(422, "Invalid JSON data")
    
    try:
        # 调用Service更新画像
        profile_data = profile_service.update_profile(user, data)
        return JsonResponse(profile_data, status=200)
    
    except ValueError as e:
        # 数据验证失败
        return JsonResponse({
            "error": {
                "code": "validation_error",
                "message": "参数校验失败",
                "details": e.args[0] if e.args else {}
            }
        }, status=422)
    
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
def replace_user_profile(request):
    """
    覆盖式更新用户画像（完整替换）
    PUT /users/me/profile
    
    Request Body:
        {
            "gender": "female",
            "age": 20,
            "grade": "大二",
            "college": "计算机学院",
            "major": "计算机科学与技术",
            "mbti": "INTJ",
            "interests": ["人工智能", "德语"],
            "organizations": ["学生会"],
            "consumption_preferences": ["数码", "奶茶"],
            "career_intentions": ["大厂"],
            "skills": ["Python"],
            "current_status": "备战期末"
        }
    
    Response:
        200: 更新成功，返回完整画像
        401: 未认证
        422: 数据验证失败
    
    内部函数，由user_profile_handler调用
    """
    # 认证检查
    user, err = require_auth(request)
    if err:
        return err
    
    # 解析请求数据
    data = parse_json(request)
    if not data:
        return error(422, "Invalid JSON data")
    
    try:
        # 调用Service执行完整替换
        profile_data = profile_service.replace_profile(user, data)
        return JsonResponse(profile_data, status=200)
    
    except ValueError as e:
        # 数据验证失败
        return JsonResponse({
            "error": {
                "code": "validation_error",
                "message": "参数校验失败",
                "details": e.args[0] if e.args else {}
            }
        }, status=422)
    
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
def search_matching_profiles(request):
    """
    搜索匹配的用户画像（用于推荐）
    GET /users/me/profile/matches
    
    Query Params:
        college: 学院（可选）
        major: 专业（可选）
        mbti: MBTI类型（可选）
        min_completion: 最小完成度（可选）
    
    Response:
        200: 匹配的画像列表
        401: 未认证
    """
    if request.method != "GET":
        return error(405, "Method not allowed")
    
    # 认证检查
    user, err = require_auth(request)
    if err:
        return err
    
    # 解析查询参数
    criteria = {}
    if 'college' in request.GET:
        criteria['college'] = request.GET['college']
    if 'major' in request.GET:
        criteria['major'] = request.GET['major']
    if 'mbti' in request.GET:
        criteria['mbti'] = request.GET['mbti']
    if 'min_completion' in request.GET:
        try:
            criteria['min_completion'] = int(request.GET['min_completion'])
        except ValueError:
            pass
    
    try:
        # 调用Service搜索匹配画像
        matches = profile_service.search_matching_profiles(user, criteria)
        return JsonResponse({'matches': matches}, status=200)
    
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")
