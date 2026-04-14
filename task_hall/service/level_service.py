"""
等级与任务系统 Service

设计约定：
- EXP 直接复用 AppUser.activity_points（不新增字段）
- 等级表硬编码（30 级），无需 DB 存储
- 任务定义硬编码，TaskCompletion 只记录进度与领取状态
- period_key: 日任务 = 'YYYY-MM-DD'，周任务 = 'YYYY-WNN'
- 8个称号，每4-5级变化，越往后升级所需经验越多
"""

from django.db import transaction
from django.utils import timezone

from core.models import AppUser, PointsLog, TaskCompletion

# ─── 等级配置（30级 + 8称号）────────────────────────────────────────────────
# 每级所需经验 = round(前一级 * 1.15)，约每3-4级翻倍
# 称号每4-5级变化一次
LEVEL_TABLE = [
    {"level": 1,  "required_exp": 0,     "title": "新手探索者"},
    {"level": 2,  "required_exp": 50,    "title": "新手探索者"},
    {"level": 3,  "required_exp": 110,   "title": "新手探索者"},
    {"level": 4,  "required_exp": 180,   "title": "新手探索者"},
    {"level": 5,  "required_exp": 260,   "title": "新手探索者"},
    {"level": 6,  "required_exp": 350,   "title": "问卷新人"},
    {"level": 7,  "required_exp": 460,   "title": "问卷新人"},
    {"level": 8,  "required_exp": 590,   "title": "问卷新人"},
    {"level": 9,  "required_exp": 750,   "title": "问卷新人"},
    {"level": 10, "required_exp": 940,   "title": "问卷新人"},
    {"level": 11, "required_exp": 1180,  "title": "活跃参与者"},
    {"level": 12, "required_exp": 1470,  "title": "活跃参与者"},
    {"level": 13, "required_exp": 1820,  "title": "活跃参与者"},
    {"level": 14, "required_exp": 2240,  "title": "活跃参与者"},
    {"level": 15, "required_exp": 2740,  "title": "活跃参与者"},
    {"level": 16, "required_exp": 3350,  "title": "数据先锋"},
    {"level": 17, "required_exp": 4090,  "title": "数据先锋"},
    {"level": 18, "required_exp": 4980,  "title": "数据先锋"},
    {"level": 19, "required_exp": 6070,  "title": "数据先锋"},
    {"level": 20, "required_exp": 7390,  "title": "数据先锋"},
    {"level": 21, "required_exp": 9000,  "title": "调研专家"},
    {"level": 22, "required_exp": 10960, "title": "调研专家"},
    {"level": 23, "required_exp": 13350, "title": "调研专家"},
    {"level": 24, "required_exp": 16260, "title": "调研专家"},
    {"level": 25, "required_exp": 19810, "title": "调研专家"},
    {"level": 26, "required_exp": 24140, "title": "问卷大师"},
    {"level": 27, "required_exp": 29400, "title": "问卷大师"},
    {"level": 28, "required_exp": 35820, "title": "问卷大师"},
    {"level": 29, "required_exp": 43620, "title": "问卷大师"},
    {"level": 30, "required_exp": 53140, "title": "问卷大师"},
]

# ─── 任务定义 ────────────────────────────────────────────────────────────────
# target_count: 达成所需进度
# reward_exp / reward_points: 领取奖励数值
TASK_DEFINITIONS = {
    "daily_login":     {"type": "daily",  "desc": "今日登录平台",      "target": 1,  "reward_exp": 10,  "reward_points": 1},
    "daily_fill_1":    {"type": "daily",  "desc": "完成1份问卷",       "target": 1,  "reward_exp": 20,  "reward_points": 2},
    "daily_fill_3":    {"type": "daily",  "desc": "完成3份问卷",       "target": 3,  "reward_exp": 50,  "reward_points": 5},
    "weekly_fill_10":  {"type": "weekly", "desc": "本周完成10份问卷",  "target": 10, "reward_exp": 150, "reward_points": 15},
    "weekly_publish_1": {"type": "weekly", "desc": "本周发布1份问卷",  "target": 1,  "reward_exp": 80,  "reward_points": 8},
}


class LevelServiceError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class LevelService:

    # ─── 等级计算 ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_level_info(user):
        exp = user.activity_points
        current = LEVEL_TABLE[0]
        next_level = None
        for i, row in enumerate(LEVEL_TABLE):
            if exp >= row["required_exp"]:
                current = row
                if i + 1 < len(LEVEL_TABLE):
                    next_level = LEVEL_TABLE[i + 1]
            else:
                break

        exp_in_level = exp - current["required_exp"]
        exp_to_next = (next_level["required_exp"] - current["required_exp"]) if next_level else 0
        progress_pct = round(exp_in_level / exp_to_next * 100) if exp_to_next else 100

        return {
            "exp": exp,
            "level": current["level"],
            "title": current["title"],
            "exp_in_level": exp_in_level,
            "exp_to_next": exp_to_next,
            "progress_pct": progress_pct,
            "is_max_level": next_level is None,
            "next_level": next_level["level"] if next_level else None,
            "next_title": next_level["title"] if next_level else None,
        }

    # ─── 周期 key ─────────────────────────────────────────────────────────────

    @staticmethod
    def today_key():
        return timezone.now().date().isoformat()

    @staticmethod
    def week_key():
        now = timezone.now().date()
        return f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"

    # ─── 任务列表查询 ─────────────────────────────────────────────────────────

    @staticmethod
    def _get_tasks(user, task_type):
        period_key = LevelService.today_key() if task_type == "daily" else LevelService.week_key()
        codes = [c for c, d in TASK_DEFINITIONS.items() if d["type"] == task_type]

        completions = {
            tc.task_code: tc
            for tc in TaskCompletion.objects.filter(
                user=user, task_code__in=codes, period_key=period_key
            )
        }

        items = []
        for code in codes:
            defn = TASK_DEFINITIONS[code]
            tc = completions.get(code)
            progress = tc.progress if tc else 0
            completed = tc.completed if tc else False
            claimed = tc.claimed if tc else False
            if not completed and progress >= defn["target"]:
                completed = True
            items.append({
                "code": code,
                "desc": defn["desc"],
                "target": defn["target"],
                "progress": progress,
                "completed": completed,
                "claimed": claimed,
                "reward_exp": defn["reward_exp"],
                "reward_points": defn["reward_points"],
                "claimable": completed and not claimed,
            })
        return {"period_key": period_key, "tasks": items}

    @staticmethod
    def get_daily_tasks(user):
        return LevelService._get_tasks(user, "daily")

    @staticmethod
    def get_weekly_tasks(user):
        return LevelService._get_tasks(user, "weekly")

    # ─── 任务进度更新（内部调用） ──────────────────────────────────────────────

    @staticmethod
    def increment_task(user, task_code, amount=1):
        """增加某任务当前周期的进度，幂等（已 claimed 不再更新）。"""
        defn = TASK_DEFINITIONS.get(task_code)
        if not defn:
            return
        period_key = (
            LevelService.today_key()
            if defn["type"] == "daily"
            else LevelService.week_key()
        )
        tc, _ = TaskCompletion.objects.get_or_create(
            user=user,
            task_code=task_code,
            period_key=period_key,
            defaults={"progress": 0, "completed": False, "claimed": False},
        )
        if tc.claimed:
            return
        tc.progress = min(tc.progress + amount, defn["target"])
        if tc.progress >= defn["target"]:
            tc.completed = True
        tc.save(update_fields=["progress", "completed", "updated_at"])

    # ─── 登录打卡（在视图层调用） ─────────────────────────────────────────────

    @staticmethod
    def mark_login(user):
        LevelService.increment_task(user, "daily_login")

    # ─── 填写问卷后更新 ───────────────────────────────────────────────────────

    @staticmethod
    def on_fill_submitted(user):
        LevelService.increment_task(user, "daily_fill_1")
        LevelService.increment_task(user, "daily_fill_3")
        LevelService.increment_task(user, "weekly_fill_10")

    # ─── 发布问卷后更新 ───────────────────────────────────────────────────────

    @staticmethod
    def on_survey_published(user):
        LevelService.increment_task(user, "weekly_publish_1")

    # ─── 领取奖励 ─────────────────────────────────────────────────────────────

    @staticmethod
    def claim_task(user, task_code):
        defn = TASK_DEFINITIONS.get(task_code)
        if not defn:
            raise LevelServiceError(404, "任务不存在")
        period_key = (
            LevelService.today_key()
            if defn["type"] == "daily"
            else LevelService.week_key()
        )
        tc = TaskCompletion.objects.filter(
            user=user, task_code=task_code, period_key=period_key
        ).first()
        if not tc or not tc.completed:
            raise LevelServiceError(403, "任务尚未完成，无法领取")
        if tc.claimed:
            raise LevelServiceError(409, "奖励已领取")

        with transaction.atomic():
            user_obj = user.__class__.objects.select_for_update().get(pk=user.pk)
            if defn["reward_exp"] > 0:
                user_obj.activity_points += defn["reward_exp"]
            if defn["reward_points"] > 0:
                user_obj.points += defn["reward_points"]
            fields = ["activity_points"]
            if defn["reward_points"] > 0:
                fields.append("points")
            user_obj.save(update_fields=fields)
            if defn["reward_points"] > 0:
                PointsLog.objects.create(
                    user=user_obj,
                    points_type="task_reward",
                    delta=defn["reward_points"],
                    reason=f"完成任务「{defn['desc']}」奖励",
                    ref_type="task",
                    ref_id=0,
                )
            tc.claimed = True
            tc.save(update_fields=["claimed", "updated_at"])

        return {
            "task_code": task_code,
            "reward_exp": defn["reward_exp"],
            "reward_points": defn["reward_points"],
            "level_info": LevelService.get_level_info(user_obj),
        }
