from django.utils import timezone
from core.models import AppUser, UserTag, Response, Survey, SurveyTag, PointsLog


class ProfileExtractorService:
    def extract_user_profile(self, user_id):
        """提取用户个人信息并拼接成字符串"""
        # 1. 获取用户基本信息
        user = AppUser.objects.get(id=user_id)
        
        # 2. 获取用户标签
        user_tags = UserTag.objects.filter(user=user).select_related('tag')
        
        # 3. 获取用户问卷记录
        responses = Response.objects.filter(user=user)
        completed_responses = responses.filter(status='completed')
        
        # 4. 获取用户填写过的问卷及标签
        completed_surveys = Survey.objects.filter(id__in=completed_responses.values('survey_id'))
        survey_type_count = self._analyze_survey_types(completed_surveys)
        
        # 5. 计算问卷完成率
        completion_rate = self._calculate_completion_rate(responses, completed_responses)
        
        # 6. 分析最近活动
        last_activity = self._analyze_last_activity(user, completed_responses)
        
        # 7. 分析积分获取渠道
        points_channels = self._analyze_points_channels(user)
        
        # 8. 计算注册时长
        registration_duration = self._calculate_registration_duration(user)
        
        # 9. 构建信息字符串
        profile_string = self._build_profile_string(
            user, user_tags, survey_type_count, completed_responses.count(),
            completion_rate, last_activity, points_channels, registration_duration
        )
        
        return profile_string
    
    def _analyze_survey_types(self, surveys):
        """分析用户填写的问卷类型及数量"""
        survey_type_count = {}
        
        for survey in surveys:
            # 获取问卷标签
            survey_tags = SurveyTag.objects.filter(survey=survey).select_related('tag')
            for survey_tag in survey_tags:
                if survey_tag.tag.type == 'survey_type':
                    tag_name = survey_tag.tag.name
                    survey_type_count[tag_name] = survey_type_count.get(tag_name, 0) + 1
        
        return survey_type_count
    
    def _calculate_completion_rate(self, all_responses, completed_responses):
        """计算问卷完成率"""
        total_count = all_responses.count()
        if total_count == 0:
            return 0
        return round((completed_responses.count() / total_count) * 100)
    
    def _analyze_last_activity(self, user, completed_responses):
        """分析用户最近活动时间"""
        if completed_responses.exists():
            last_response = completed_responses.order_by('-submitted_at').first()
            if last_response and last_response.submitted_at:
                days_since_last_activity = (timezone.now() - last_response.submitted_at).days
                if days_since_last_activity <= 7:
                    return f"{days_since_last_activity}天内"
                elif days_since_last_activity <= 30:
                    return f"{days_since_last_activity}天内"
                else:
                    return "30天前"
        
        # 基于用户更新时间
        days_since_update = (timezone.now() - user.updated_at).days
        if days_since_update <= 7:
            return f"{days_since_update}天内"
        elif days_since_update <= 30:
            return f"{days_since_update}天内"
        else:
            return "30天前"
    
    def _analyze_points_channels(self, user):
        """分析用户积分获取渠道"""
        points_logs = PointsLog.objects.filter(user=user, delta__gt=0)
        
        if not points_logs.exists():
            return {"问卷填写": 0, "其他活动": 0}
        
        channel_count = {"问卷填写": 0, "其他活动": 0}
        total_points = sum(log.delta for log in points_logs)
        
        if total_points == 0:
            return channel_count
        
        for log in points_logs:
            if '问卷' in log.reason or log.ref_type == 'survey_fill':
                channel_count["问卷填写"] += log.delta
            else:
                channel_count["其他活动"] += log.delta
        
        # 转换为百分比
        channel_percentages = {
            "问卷填写": round((channel_count["问卷填写"] / total_points) * 100),
            "其他活动": round((channel_count["其他活动"] / total_points) * 100)
        }
        
        return channel_percentages
    
    def _calculate_registration_duration(self, user):
        """计算用户注册时长"""
        days_since_registration = (timezone.now() - user.created_at).days
        
        if days_since_registration < 30:
            return f"{days_since_registration}天"
        elif days_since_registration < 365:
            months = days_since_registration // 30
            return f"{months}个月"
        else:
            years = days_since_registration // 365
            return f"{years}年"
    
    def _build_profile_string(self, user, user_tags, survey_type_count, total_surveys, 
                            completion_rate, last_activity, points_channels, registration_duration):
        """构建个人信息字符串"""
        parts = []
        
        # 用户兴趣
        interest_tags = [tag.tag.name for tag in user_tags if tag.tag.type == 'interest']
        if interest_tags:
            parts.append(f"用户兴趣：{', '.join(interest_tags)}")
        
        # 用户标签
        other_tags = [tag.tag.name for tag in user_tags if tag.tag.type != 'interest']
        if other_tags:
            parts.append(f"用户标签：{', '.join(other_tags)}")
        
        # 问卷类型统计
        if survey_type_count:
            type_str = ", ".join([f"{tag}({count})" for tag, count in survey_type_count.items()])
            parts.append(f"已填问卷类型：{type_str}")
        
        # 问卷填写统计
        if total_surveys > 0:
            parts.append(f"问卷填写总量：{total_surveys}，完成率：{completion_rate}%")
        
        # 最近活动
        parts.append(f"最近活跃：{last_activity}")
        
        # 用户活跃度
        activity_level = "高" if user.activity_points > 800 else "中" if user.activity_points > 300 else "低"
        parts.append(f"用户活跃度：{activity_level}（{user.activity_points}/1000）")
        
        # 信用评分
        credit_level = "优秀" if user.credit_score > 90 else "良好" if user.credit_score > 70 else "一般"
        parts.append(f"信用评分：{credit_level}（{user.credit_score}/100）")
        
        # 注册时长
        parts.append(f"注册时长：{registration_duration}")
        
        # 积分获取渠道
        if points_channels["问卷填写"] > 0 or points_channels["其他活动"] > 0:
            channel_str = f"问卷填写({points_channels['问卷填写']}%), 其他活动({points_channels['其他活动']}%)"
            parts.append(f"积分获取渠道：{channel_str}")
        
        return "\n".join(parts)
