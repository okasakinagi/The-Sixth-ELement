from django.http import JsonResponse
from user_profile_extractor.service.profile_extractor_service import ProfileExtractorService

# 导入认证相关函数（从现有的模块中）
from core.views import error, internal_error, require_auth, parse_json


def get_user_profile_summary(request):
    """
    获取用户个人信息摘要
    GET /api/v1/profile/summary
    """
    if request.method != "GET":
        return error(405, "Method not allowed")
    
    # 验证用户认证
    user, err = require_auth(request)
    if err:
        return err
    
    try:
        # 创建服务实例
        service = ProfileExtractorService()
        
        # 提取用户个人信息
        profile_summary = service.extract_user_profile(user.id)
        
        # 返回响应
        return JsonResponse({
            "profile_summary": profile_summary,
            "user": {
                "id": user.id,
                "nickname": user.nickname,
                "email": user.email
            }
        }, status=200)
    except Exception as exc:
        return internal_error(exc)
