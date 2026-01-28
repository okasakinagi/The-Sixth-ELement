"""
UserProfile Mapper - 数据访问层
基于Tag系统实现用户画像的数据访问
"""
from django.db import transaction
from core.models import AppUser, Tag, UserTag


class UserProfileMapper:
    """用户画像数据访问映射器（基于Tag系统）"""
    
    # 标签类型常量（对应API文档中的画像字段）
    TAG_TYPE_GENDER = "gender"
    TAG_TYPE_AGE = "age"
    TAG_TYPE_GRADE = "grade"
    TAG_TYPE_COLLEGE = "college"
    TAG_TYPE_MAJOR = "major"
    TAG_TYPE_MBTI = "mbti"
    TAG_TYPE_INTEREST = "interest"  # 兴趣爱好
    TAG_TYPE_ORGANIZATION = "organization"  # 组织/社团
    TAG_TYPE_CONSUMPTION = "consumption"  # 消费偏好
    TAG_TYPE_CAREER = "career"  # 职业意向
    TAG_TYPE_SKILL = "skill"  # 技能
    TAG_TYPE_STATUS = "status"  # 当前状态
    
    @staticmethod
    def get_user_tags(user, tag_type=None):
        """
        获取用户的标签
        
        Args:
            user: AppUser实例
            tag_type: 标签类型（可选，不传则返回所有）
            
        Returns:
            QuerySet of Tag
        """
        queryset = Tag.objects.filter(usertag__user=user)
        if tag_type:
            queryset = queryset.filter(type=tag_type)
        return queryset.order_by('type', 'name')
    
    @staticmethod
    def get_user_profile_dict(user):
        """
        获取用户画像（以字典形式返回，按类型组织）
        
        Args:
            user: AppUser实例
            
        Returns:
            dict: 画像数据
        """
        user_tags = UserTag.objects.filter(user_id=user.id).select_related('tag')
        
        profile = {
            'user_id': user.id,
            'gender': None,
            'age': None,
            'grade': None,
            'college': None,
            'major': None,
            'mbti': None,
            'interests': [],
            'organizations': [],
            'consumption_preferences': [],
            'career_intention': [],
            'skills': [],
            'current_status': None,
        }
        
        for user_tag in user_tags:
            tag = user_tag.tag
            tag_type = tag.type
            tag_name = tag.name
            
            # 单值字段（取第一个标签的值）
            if tag_type == UserProfileMapper.TAG_TYPE_GENDER and not profile['gender']:
                profile['gender'] = tag_name
            elif tag_type == UserProfileMapper.TAG_TYPE_AGE and not profile['age']:
                try:
                    profile['age'] = int(tag_name)
                except (ValueError, TypeError):
                    pass
            elif tag_type == UserProfileMapper.TAG_TYPE_GRADE and not profile['grade']:
                profile['grade'] = tag_name
            elif tag_type == UserProfileMapper.TAG_TYPE_COLLEGE and not profile['college']:
                profile['college'] = tag_name
            elif tag_type == UserProfileMapper.TAG_TYPE_MAJOR and not profile['major']:
                profile['major'] = tag_name
            elif tag_type == UserProfileMapper.TAG_TYPE_MBTI and not profile['mbti']:
                profile['mbti'] = tag_name
            elif tag_type == UserProfileMapper.TAG_TYPE_STATUS and not profile['current_status']:
                profile['current_status'] = tag_name
            # 多值字段（数组）
            elif tag_type == UserProfileMapper.TAG_TYPE_INTEREST:
                profile['interests'].append(tag_name)
            elif tag_type == UserProfileMapper.TAG_TYPE_ORGANIZATION:
                profile['organizations'].append(tag_name)
            elif tag_type == UserProfileMapper.TAG_TYPE_CONSUMPTION:
                profile['consumption_preferences'].append(tag_name)
            elif tag_type == UserProfileMapper.TAG_TYPE_CAREER:
                profile['career_intention'].append(tag_name)
            elif tag_type == UserProfileMapper.TAG_TYPE_SKILL:
                profile['skills'].append(tag_name)
        
        return profile
    
    @staticmethod
    def set_user_tag(user, tag_type, tag_name):
        """
        设置用户的单个标签（单值字段，会替换同类型旧标签）
        
        Args:
            user: AppUser实例
            tag_type: 标签类型
            tag_name: 标签名称
            
        Returns:
            Tag实例
        """
        with transaction.atomic():
            # 删除同类型的旧标签
            UserTag.objects.filter(user_id=user.id, tag__type=tag_type).delete()
            
            if tag_name:
                # 创建或获取标签
                tag, _ = Tag.objects.get_or_create(name=tag_name, type=tag_type)
                # 创建用户标签关联
                UserTag.objects.create(user=user, tag=tag)
                return tag
            return None
    
    @staticmethod
    def set_user_tags_multi(user, tag_type, tag_names):
        """
        设置用户的多个标签（多值字段，会替换同类型所有旧标签）
        
        Args:
            user: AppUser实例
            tag_type: 标签类型
            tag_names: 标签名称列表
            
        Returns:
            list of Tag
        """
        with transaction.atomic():
            # 删除同类型的旧标签
            UserTag.objects.filter(user_id=user.id, tag__type=tag_type).delete()
            
            tags = []
            if tag_names:
                for tag_name in tag_names:
                    if tag_name:
                        tag, _ = Tag.objects.get_or_create(name=tag_name, type=tag_type)
                        UserTag.objects.create(user=user, tag=tag)
                        tags.append(tag)
            return tags
    
    @staticmethod
    def update_user_profile(user, profile_data):
        """
        更新用户画像（部分更新）
        
        Args:
            user: AppUser实例
            profile_data: dict, 画像数据
            
        Returns:
            dict: 更新后的画像
        """
        with transaction.atomic():
            # 单值字段
            if 'gender' in profile_data:
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_GENDER, profile_data['gender'])
            if 'age' in profile_data:
                age_str = str(profile_data['age']) if profile_data['age'] is not None else None
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_AGE, age_str)
            if 'grade' in profile_data:
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_GRADE, profile_data['grade'])
            if 'college' in profile_data:
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_COLLEGE, profile_data['college'])
            if 'major' in profile_data:
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_MAJOR, profile_data['major'])
            if 'mbti' in profile_data:
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_MBTI, profile_data['mbti'])
            if 'current_status' in profile_data:
                UserProfileMapper.set_user_tag(user, UserProfileMapper.TAG_TYPE_STATUS, profile_data['current_status'])
            
            # 多值字段（数组）
            if 'interests' in profile_data:
                UserProfileMapper.set_user_tags_multi(user, UserProfileMapper.TAG_TYPE_INTEREST, profile_data['interests'])
            if 'organizations' in profile_data:
                UserProfileMapper.set_user_tags_multi(user, UserProfileMapper.TAG_TYPE_ORGANIZATION, profile_data['organizations'])
            if 'consumption_preferences' in profile_data:
                UserProfileMapper.set_user_tags_multi(user, UserProfileMapper.TAG_TYPE_CONSUMPTION, profile_data['consumption_preferences'])
            if 'career_intention' in profile_data:
                UserProfileMapper.set_user_tags_multi(user, UserProfileMapper.TAG_TYPE_CAREER, profile_data['career_intention'])
            if 'skills' in profile_data:
                UserProfileMapper.set_user_tags_multi(user, UserProfileMapper.TAG_TYPE_SKILL, profile_data['skills'])
            
            return UserProfileMapper.get_user_profile_dict(user)
    
    @staticmethod
    def delete_user_profile(user):
        """
        删除用户所有画像标签
        
        Args:
            user: AppUser实例
            
        Returns:
            int: 删除的标签数量
        """
        profile_tag_types = [
            UserProfileMapper.TAG_TYPE_GENDER,
            UserProfileMapper.TAG_TYPE_AGE,
            UserProfileMapper.TAG_TYPE_GRADE,
            UserProfileMapper.TAG_TYPE_COLLEGE,
            UserProfileMapper.TAG_TYPE_MAJOR,
            UserProfileMapper.TAG_TYPE_MBTI,
            UserProfileMapper.TAG_TYPE_INTEREST,
            UserProfileMapper.TAG_TYPE_ORGANIZATION,
            UserProfileMapper.TAG_TYPE_CONSUMPTION,
            UserProfileMapper.TAG_TYPE_CAREER,
            UserProfileMapper.TAG_TYPE_SKILL,
            UserProfileMapper.TAG_TYPE_STATUS,
        ]
        count, _ = UserTag.objects.filter(user_id=user.id, tag__type__in=profile_tag_types).delete()
        return count
    
    @staticmethod
    def search_users_by_tags(tag_criteria, exclude_user=None):
        """
        根据标签搜索用户（用于匹配推荐）
        
        Args:
            tag_criteria: dict, 标签条件
                {
                    'college': '计算机学院',
                    'major': '计算机',
                    'mbti': 'INTJ'
                }
            exclude_user: AppUser实例，要排除的用户
            
        Returns:
            QuerySet of AppUser
        """
        queryset = AppUser.objects.all()
        
        if 'college' in tag_criteria and tag_criteria['college']:
            queryset = queryset.filter(
                usertag__tag__type=UserProfileMapper.TAG_TYPE_COLLEGE,
                usertag__tag__name__icontains=tag_criteria['college']
            )
        
        if 'major' in tag_criteria and tag_criteria['major']:
            queryset = queryset.filter(
                usertag__tag__type=UserProfileMapper.TAG_TYPE_MAJOR,
                usertag__tag__name__icontains=tag_criteria['major']
            )
        
        if 'mbti' in tag_criteria and tag_criteria['mbti']:
            queryset = queryset.filter(
                usertag__tag__type=UserProfileMapper.TAG_TYPE_MBTI,
                usertag__tag__name=tag_criteria['mbti']
            )
        
        if 'gender' in tag_criteria and tag_criteria['gender']:
            queryset = queryset.filter(
                usertag__tag__type=UserProfileMapper.TAG_TYPE_GENDER,
                usertag__tag__name=tag_criteria['gender']
            )
        
        if exclude_user:
            queryset = queryset.exclude(id=exclude_user.id)
        
        return queryset.distinct()
