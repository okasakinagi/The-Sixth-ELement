from django.urls import path
from .controllers import profile_controller

urlpatterns = [
    # 用户画像API (在controller中根据HTTP方法路由)
    path("users/me/profile", profile_controller.user_profile_handler),  # GET/PATCH/PUT
    
    # 匹配推荐（可选功能）
    path("users/me/profile/matches", profile_controller.search_matching_profiles),  # GET
]
