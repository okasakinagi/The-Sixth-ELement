"""
风控规则引擎服务。
"""
import json
from datetime import datetime, timedelta
from django.db.models import Q, Count, F
from core.models import RiskRule, RiskEvent, AppUser, Survey, Response


class RiskEngine:
    """风控规则引擎。"""

    @classmethod
    def evaluate_submission(cls, user=None, survey=None, ip_address=None, device_id=None, duration_seconds=0, answers=None):
        """
        评估一次提交是否触发风控规则。
        
        Args:
            user: 用户对象（AppUser）
            survey: 问卷对象（Survey）
            ip_address: IP地址
            device_id: 设备ID
            duration_seconds: 填写时长（秒）
            answers: 用户答案列表，用于检测固定答案模式
            
        Returns:
            list: 触发的规则列表
        """
        triggered_rules = []
        context = {
            "user": user,
            "survey": survey,
            "ip_address": ip_address,
            "device_id": device_id,
            "duration_seconds": duration_seconds,
            "answers": answers or [],
            "now": datetime.now(),
        }

        enabled_rules = RiskRule.get_enabled_rules()
        for rule in enabled_rules:
            try:
                if cls._check_rule(rule, context):
                    triggered_rules.append(rule)
                    cls._handle_rule_actions(rule, context)
            except Exception as e:
                print(f"风控规则执行失败 {rule.rule_code}: {e}")

        return triggered_rules

    @classmethod
    def _check_rule(cls, rule, context):
        """检查规则是否触发。"""
        event_type = rule.event_type
        conditions = rule.conditions or {}

        if event_type == "short_duration":
            return cls._check_short_duration(conditions, context)
        elif event_type == "ip_anomaly":
            return cls._check_ip_anomaly(conditions, context)
        elif event_type == "device_anomaly":
            return cls._check_device_anomaly(conditions, context)
        elif event_type == "time_anomaly":
            return cls._check_time_anomaly(conditions, context)
        elif event_type == "fixed_answer":
            return cls._check_fixed_answer(conditions, context)
        else:
            return False

    @classmethod
    def _check_short_duration(cls, conditions, context):
        """检查短时长回答。"""
        threshold = conditions.get("duration_threshold", 30)
        duration = context.get("duration_seconds", 0)
        return duration < threshold

    @classmethod
    def _check_ip_anomaly(cls, conditions, context):
        """检查IP异常：同一IP N分钟内注册>10次，或同一IP N分钟内提交>50份。"""
        ip_address = context.get("ip_address")
        if not ip_address:
            return False

        window_minutes = conditions.get("window_minutes", 60)
        registration_threshold = conditions.get("registration_threshold", 10)
        submission_threshold = conditions.get("submission_threshold", 50)

        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        ip_registrations = AppUser.objects.filter(
            created_at__gte=cutoff_time,
        ).filter(
            Q(profile_json__contains={"ip": ip_address}) if hasattr(AppUser, "profile_json") else Q(pk=-1)
        ).count()

        ip_submissions = Response.objects.filter(
            created_at__gte=cutoff_time,
            detail__contains={"ip": ip_address} if hasattr(Response, "detail") else Q(pk=-1)
        ).count()

        return (ip_registrations >= registration_threshold) or (ip_submissions >= submission_threshold)

    @classmethod
    def _check_device_anomaly(cls, conditions, context):
        """检查设备异常：同一设备N天内提交>50份。"""
        device_id = context.get("device_id")
        if not device_id:
            return False

        window_days = conditions.get("window_days", 7)
        submission_threshold = conditions.get("submission_threshold", 50)

        cutoff_time = datetime.now() - timedelta(days=window_days)

        device_submissions = Response.objects.filter(
            created_at__gte=cutoff_time,
            detail__contains={"device_id": device_id} if hasattr(Response, "detail") else Q(pk=-1)
        ).count()

        return device_submissions >= submission_threshold

    @classmethod
    def _check_time_anomaly(cls, conditions, context):
        """检查异常时间：凌晨2-5点大量提交。"""
        start_hour = conditions.get("start_hour", 2)
        end_hour = conditions.get("end_hour", 5)
        threshold_submissions = conditions.get("threshold_submissions", 5)
        window_minutes = conditions.get("window_minutes", 30)

        now = datetime.now()
        hour = now.hour

        if not (start_hour <= hour < end_hour):
            return False

        user = context.get("user")
        if not user:
            return False

        cutoff_time = now - timedelta(minutes=window_minutes)
        recent_submissions = Response.objects.filter(
            user=user,
            created_at__gte=cutoff_time
        ).count()

        return recent_submissions >= threshold_submissions

    @classmethod
    def _check_fixed_answer(cls, conditions, context):
        """检查固定答案：连续N题选择同一选项。"""
        answers = context.get("answers", [])
        if len(answers) < 3:
            return False

        consecutive_threshold = conditions.get("consecutive_threshold", 3)
        consecutive_count = 0
        last_answer = None

        for answer in answers:
            if answer == last_answer:
                consecutive_count += 1
            else:
                consecutive_count = 1
            last_answer = answer

            if consecutive_count >= consecutive_threshold:
                return True

        return False

    @classmethod
    def _handle_rule_actions(cls, rule, context):
        """处理规则触发后的动作。"""
        user = context.get("user")
        survey = context.get("survey")
        actions = rule.actions or []

        RiskEvent.objects.create(
            user=user,
            survey=survey,
            event_type=rule.event_type,
            severity=rule.severity,
            detail={
                "rule_code": rule.rule_code,
                "rule_name": rule.rule_name,
                "conditions": rule.conditions,
                "actions": actions,
                "ip_address": context.get("ip_address"),
                "device_id": context.get("device_id"),
                "duration_seconds": context.get("duration_seconds"),
            }
        )

        for action in actions:
            cls._execute_action(action, user)

    @classmethod
    def _execute_action(cls, action, user):
        """执行单个动作。"""
        if action == "log":
            pass
        elif action == "mark_suspicious":
            if user:
                user.status = "suspicious"
                user.save()
        elif action == "restrict_user":
            if user:
                user.status = "restricted"
                user.save()
        elif action == "alert_admin":
            pass

    @classmethod
    def initialize_default_rules(cls):
        """初始化默认的风控规则（仅记录日志，不自动处罚）。"""
        default_rules = [
            {
                "rule_code": "short_duration_30s",
                "rule_name": "短时长回答（<30秒）",
                "description": "用户在30秒内完成问卷填写，仅记录供管理员参考",
                "enabled": True,
                "priority": 10,
                "event_type": "short_duration",
                "severity": "medium",
                "conditions": {"duration_threshold": 30},
                "actions": ["log"]
            },
            {
                "rule_code": "short_duration_10s",
                "rule_name": "极短时长回答（<10秒）",
                "description": "用户在10秒内完成问卷填写，仅记录供管理员参考",
                "enabled": True,
                "priority": 5,
                "event_type": "short_duration",
                "severity": "high",
                "conditions": {"duration_threshold": 10},
                "actions": ["log"]
            },
            {
                "rule_code": "time_anomaly_night",
                "rule_name": "凌晨异常时间检测",
                "description": "用户在凌晨2-5点大量提交问卷，仅记录供管理员参考",
                "enabled": True,
                "priority": 50,
                "event_type": "time_anomaly",
                "severity": "medium",
                "conditions": {
                    "start_hour": 2,
                    "end_hour": 5,
                    "threshold_submissions": 5,
                    "window_minutes": 30
                },
                "actions": ["log"]
            },
            {
                "rule_code": "fixed_answer_detection",
                "rule_name": "固定答案模式检测",
                "description": "连续3题选择同一选项，仅记录供管理员参考",
                "enabled": True,
                "priority": 60,
                "event_type": "fixed_answer",
                "severity": "low",
                "conditions": {"consecutive_threshold": 3},
                "actions": ["log"]
            },
        ]

        created_count = 0
        for rule_data in default_rules:
            rule, created = RiskRule.objects.get_or_create(
                rule_code=rule_data["rule_code"],
                defaults=rule_data
            )
            if created:
                created_count += 1
                print(f"创建风控规则: {rule.rule_name}")

        return created_count