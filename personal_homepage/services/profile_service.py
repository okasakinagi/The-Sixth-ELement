"""
UserProfile Service - 业务逻辑层
处理用户画像相关的业务逻辑、数据验证和格式转换（基于Tag系统）
"""

from datetime import timezone as dt_timezone
from ..mapper.profile_mapper import UserProfileMapper


class UserProfileService:
    """用户画像业务逻辑服务"""

    def __init__(self):
        self.mapper = UserProfileMapper()

    def get_profile(self, user):
        """
        获取用户画像

        Args:
            user: AppUser实例

        Returns:
            dict: 画像数据（包含profile_completion字段）
        """
        profile = self.mapper.get_user_profile_dict(user)

        # 计算完成度
        profile["profile_completion"] = self._calculate_completion(profile)

        # 添加更新时间（从UserTag获取最新时间）
        from core.models import UserTag

        latest_tag = (
            UserTag.objects.filter(user_id=user.id).order_by("-created_at").first()
        )
        profile["updated_at"] = (
            latest_tag.created_at.astimezone(dt_timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
            if latest_tag
            else None
        )

        return profile

    def update_profile(self, user, profile_data):
        """
        更新用户画像（PATCH - 部分更新）

        Args:
            user: AppUser实例
            profile_data: dict, 要更新的字段

        Returns:
            dict: 更新后的画像数据

        Raises:
            ValueError: 数据验证失败
        """
        validated_data = self._validate_profile_data(profile_data, partial=True)

        self.mapper.update_user_profile(user, validated_data)

        user.calculate_profile_completion()

        return self.get_profile(user)

    def replace_profile(self, user, profile_data):
        """
        覆盖式更新用户画像（PUT - 完整替换）

        Args:
            user: AppUser实例
            profile_data: dict, 完整的画像数据

        Returns:
            dict: 更新后的画像数据

        Raises:
            ValueError: 数据验证失败
        """
        validated_data = self._validate_profile_data(profile_data, partial=False)

        self.mapper.delete_user_profile(user)

        self.mapper.update_user_profile(user, validated_data)

        user.calculate_profile_completion()

        return self.get_profile(user)

    def _validate_profile_data(self, data, partial=True):
        """
        验证画像数据

        Args:
            data: dict, 待验证的数据
            partial: bool, 是否为部分更新

        Returns:
            dict: 验证后的数据

        Raises:
            ValueError: 验证失败
        """
        errors = {}
        validated = {}

        # 兼容历史字段名：career_intentions -> career_intention
        if "career_intentions" in data and "career_intention" not in data:
            data = {**data, "career_intention": data.get("career_intentions")}

        # 兼容前端 camelCase 字段名
        camel_to_snake_map = {
            "consumptionPreferences": "consumption_preferences",
            "careerIntention": "career_intention",
            "currentStatus": "current_status",
        }
        normalized_data = dict(data)
        for camel_key, snake_key in camel_to_snake_map.items():
            if camel_key in normalized_data and snake_key not in normalized_data:
                normalized_data[snake_key] = normalized_data.get(camel_key)
        data = normalized_data

        # 验证gender（支持中文和英文）
        if "gender" in data:
            valid_genders = [
                None,
                "",
                "male",
                "female",
                "other",
                "secret",
                "男",
                "女",
                "其他",
                "保密",
            ]
            if data["gender"] not in valid_genders:
                errors["gender"] = "Invalid gender value"
            else:
                validated["gender"] = data["gender"] if data["gender"] else None

        # 验证age
        if "age" in data:
            age = data["age"]
            if age is not None:
                try:
                    age = int(age)
                    if age < 0 or age > 120:
                        errors["age"] = "Age must be between 0 and 120"
                    else:
                        validated["age"] = age
                except (ValueError, TypeError):
                    errors["age"] = "Age must be a number"
            else:
                validated["age"] = None

        # 验证字符串长度
        string_fields = {
            "grade": 10,
            "college": 50,
            "major": 50,
            "current_status": 100,
        }

        for field, max_length in string_fields.items():
            if field in data:
                value = data[field]
                if value and len(str(value)) > max_length:
                    errors[field] = f"Max length is {max_length}"
                else:
                    validated[field] = value if value else None

        # 验证MBTI
        if "mbti" in data:
            mbti = data["mbti"]
            valid_mbti = [
                "INTJ",
                "INTP",
                "ENTJ",
                "ENTP",
                "INFJ",
                "INFP",
                "ENFJ",
                "ENFP",
                "ISTJ",
                "ISFJ",
                "ESTJ",
                "ESFJ",
                "ISTP",
                "ISFP",
                "ESTP",
                "ESFP",
            ]
            if mbti and mbti not in valid_mbti:
                errors["mbti"] = (
                    f'Invalid MBTI type. Must be one of: {", ".join(valid_mbti)}'
                )
            else:
                validated["mbti"] = mbti if mbti else None

        # 验证数组字段
        array_fields = [
            "interests",
            "organizations",
            "consumption_preferences",
            "career_intention",
            "skills",
        ]
        for field in array_fields:
            if field in data:
                value = data[field]
                if value is None:
                    validated[field] = []
                    continue

                if isinstance(value, str):
                    normalized_items = [
                        item.strip()
                        for item in value.replace("，", ",").split(",")
                        if item and item.strip()
                    ]
                elif isinstance(value, list):
                    normalized_items = [
                        str(item).strip() for item in value if str(item).strip()
                    ]
                else:
                    errors[field] = "Must be an array"
                    continue

                if len(normalized_items) > 8:
                    errors[field] = "Array length must be <= 8"
                elif any(len(item) > 64 for item in normalized_items):
                    errors[field] = "Each item must be <= 64 characters"
                else:
                    validated[field] = normalized_items

        if errors:
            raise ValueError(errors)

        return validated

    def _calculate_completion(self, profile):
        """
        计算画像完成度

        Args:
            profile: dict, 画像数据

        Returns:
            int: 完成度（0-100）
        """
        total_fields = 11  # 总字段数（不含状态字段）
        filled_fields = 0

        # 单值字段
        if profile.get("gender"):
            filled_fields += 1
        if profile.get("age"):
            filled_fields += 1
        if profile.get("grade"):
            filled_fields += 1
        if profile.get("college"):
            filled_fields += 1
        if profile.get("major"):
            filled_fields += 1
        if profile.get("mbti"):
            filled_fields += 1

        # 数组字段
        if profile.get("interests"):
            filled_fields += 1
        if profile.get("organizations"):
            filled_fields += 1
        if profile.get("consumption_preferences"):
            filled_fields += 1
        if profile.get("career_intention"):
            filled_fields += 1
        if profile.get("skills"):
            filled_fields += 1

        return int((filled_fields / total_fields) * 100)

    def search_matching_profiles(self, user, criteria=None):
        """
        搜索匹配的用户画像（用于推荐）

        Args:
            user: AppUser实例（当前用户）
            criteria: dict, 额外的搜索条件

        Returns:
            list: 匹配的画像列表
        """
        # 获取当前用户画像
        current_profile = self.mapper.get_user_profile_dict(user)

        # 构建搜索条件
        search_criteria = criteria or {}

        # 基于当前用户画像添加匹配条件
        if current_profile.get("college"):
            search_criteria.setdefault("college", current_profile["college"])

        # 搜索用户
        users = self.mapper.search_users_by_tags(search_criteria, exclude_user=user)

        # 转换为画像字典列表
        results = []
        for matched_user in users[:10]:  # 限制返回10个
            profile = self.mapper.get_user_profile_dict(matched_user)
            profile["profile_completion"] = self._calculate_completion(profile)
            results.append(profile)

        return results
