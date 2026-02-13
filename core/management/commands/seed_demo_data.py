from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Answer,
    AppUser,
    AuthCredential,
    PointsLog,
    Question,
    Questionnaire,
    QuestionOption,
    Response,
    Survey,
)


DEMO_EMAILS = [
    "demo_owner@local.test",
    "demo_filler1@local.test",
    "demo_filler2@local.test",
]


class Command(BaseCommand):
    help = "Seed demo users, surveys and responses for local development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_demo_data()

        users = self._seed_users()
        surveys = self._seed_surveys(users)
        self._seed_responses(users, surveys)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Users:")
        self.stdout.write("  - demo_owner@local.test / Demo@123456")
        self.stdout.write("  - demo_filler1@local.test / Demo@123456")
        self.stdout.write("  - demo_filler2@local.test / Demo@123456")

    def _reset_demo_data(self):
        demo_users = AppUser.objects.filter(email__in=DEMO_EMAILS)
        user_ids = list(demo_users.values_list("id", flat=True))

        demo_surveys = Survey.objects.filter(title__startswith="[DEMO]")
        survey_ids = list(demo_surveys.values_list("id", flat=True))

        questionnaire_ids = list(
            Questionnaire.objects.filter(survey_id__in=survey_ids).values_list("id", flat=True)
        )
        response_ids = list(
            Response.objects.filter(survey_id__in=survey_ids).values_list("id", flat=True)
        )

        Answer.objects.filter(response_id__in=response_ids).delete()
        QuestionOption.objects.filter(question_id__in=Question.objects.filter(questionnaire_id__in=questionnaire_ids).values_list("id", flat=True)).delete()
        Question.objects.filter(questionnaire_id__in=questionnaire_ids).delete()
        Response.objects.filter(id__in=response_ids).delete()
        Questionnaire.objects.filter(id__in=questionnaire_ids).delete()
        Survey.objects.filter(id__in=survey_ids).delete()
        PointsLog.objects.filter(user_id__in=user_ids, reason__startswith="[DEMO]").delete()
        AuthCredential.objects.filter(user_id__in=user_ids).delete()
        demo_users.delete()

    def _seed_users(self):
        users_payload = [
            {
                "email": "demo_owner@local.test",
                "nickname": "DemoOwner",
                "credit_score": 96,
                "points": 120,
                "activity_points": 30,
            },
            {
                "email": "demo_filler1@local.test",
                "nickname": "DemoFiller1",
                "credit_score": 88,
                "points": 45,
                "activity_points": 18,
            },
            {
                "email": "demo_filler2@local.test",
                "nickname": "DemoFiller2",
                "credit_score": 82,
                "points": 40,
                "activity_points": 14,
            },
        ]

        users = {}
        for payload in users_payload:
            user, created = AppUser.objects.get_or_create(
                email=payload["email"],
                defaults={
                    "nickname": payload["nickname"],
                    "credit_score": payload["credit_score"],
                    "points": payload["points"],
                    "activity_points": payload["activity_points"],
                    "status": "normal",
                },
            )
            if not created:
                user.nickname = payload["nickname"]
                user.credit_score = payload["credit_score"]
                user.points = payload["points"]
                user.activity_points = payload["activity_points"]
                user.status = "normal"
                user.save(
                    update_fields=[
                        "nickname",
                        "credit_score",
                        "points",
                        "activity_points",
                        "status",
                    ]
                )

            AuthCredential.objects.update_or_create(
                user=user,
                defaults={"password_hash": make_password("Demo@123456")},
            )
            users[payload["email"]] = user

        return users

    def _seed_surveys(self, users):
        owner = users["demo_owner@local.test"]
        now = timezone.now()

        survey_a, _ = Survey.objects.update_or_create(
            owner=owner,
            title="[DEMO] 校园学习习惯调查",
            defaults={
                "description": "用于本地联调的测试问卷 A",
                "estimated_minutes": 5,
                "difficulty": 2,
                "reward_points": 5,
                "publish_cost_points": 10,
                "deadline": now + timedelta(days=14),
                "target": 30,
                "completed": 2,
                "status": "published",
            },
        )

        qn_a, _ = Questionnaire.objects.update_or_create(
            survey=survey_a,
            version=1,
            defaults={
                "status": "published",
                "title": "[DEMO] 校园学习习惯调查 v1",
            },
        )

        q1, _ = Question.objects.update_or_create(
            questionnaire=qn_a,
            order_no=1,
            defaults={
                "type": "single",
                "title": "你常用的学习地点是？",
                "is_required": True,
            },
        )
        q2, _ = Question.objects.update_or_create(
            questionnaire=qn_a,
            order_no=2,
            defaults={
                "type": "multi",
                "title": "你常用的学习工具有哪些？",
                "is_required": True,
            },
        )
        q3, _ = Question.objects.update_or_create(
            questionnaire=qn_a,
            order_no=3,
            defaults={
                "type": "text",
                "title": "对校园学习空间有什么建议？",
                "is_required": False,
            },
        )

        self._sync_options(q1, ["图书馆", "宿舍", "教学楼自习区"])
        self._sync_options(q2, ["纸笔", "平板", "笔记软件", "AI 工具"])

        if survey_a.active_questionnaire_id != qn_a.id:
            survey_a.active_questionnaire = qn_a
            survey_a.save(update_fields=["active_questionnaire"])

        survey_b, _ = Survey.objects.update_or_create(
            owner=owner,
            title="[DEMO] 课程反馈快速问卷",
            defaults={
                "description": "用于本地联调的测试问卷 B",
                "estimated_minutes": 3,
                "difficulty": 1,
                "reward_points": 3,
                "publish_cost_points": 0,
                "deadline": now + timedelta(days=7),
                "target": 20,
                "completed": 1,
                "status": "published",
            },
        )

        qn_b, _ = Questionnaire.objects.update_or_create(
            survey=survey_b,
            version=1,
            defaults={
                "status": "published",
                "title": "[DEMO] 课程反馈快速问卷 v1",
            },
        )
        qb1, _ = Question.objects.update_or_create(
            questionnaire=qn_b,
            order_no=1,
            defaults={
                "type": "single",
                "title": "这门课程整体满意度？",
                "is_required": True,
            },
        )
        self._sync_options(qb1, ["很满意", "一般", "需要改进"])

        if survey_b.active_questionnaire_id != qn_b.id:
            survey_b.active_questionnaire = qn_b
            survey_b.save(update_fields=["active_questionnaire"])

        return {
            "survey_a": (survey_a, qn_a, [q1, q2, q3]),
            "survey_b": (survey_b, qn_b, [qb1]),
        }

    def _seed_responses(self, users, surveys):
        filler1 = users["demo_filler1@local.test"]
        filler2 = users["demo_filler2@local.test"]

        survey_a, qn_a, questions_a = surveys["survey_a"]
        q1, q2, q3 = questions_a

        r1, _ = Response.objects.update_or_create(
            survey=survey_a,
            questionnaire=qn_a,
            user=filler1,
            defaults={
                "status": "submitted",
                "started_at": timezone.now() - timedelta(minutes=20),
                "submitted_at": timezone.now() - timedelta(minutes=12),
                "duration_seconds": 480,
                "risk_flag": False,
                "device_fingerprint": "demo_device_1",
                "ip_hash": "demo_ip_hash_1",
            },
        )
        self._upsert_answer(r1, q1, value_text="图书馆")
        self._upsert_answer(r1, q2, value_json=["笔记软件", "AI 工具"])
        self._upsert_answer(r1, q3, value_text="希望晚上开放到更晚。")

        r2, _ = Response.objects.update_or_create(
            survey=survey_a,
            questionnaire=qn_a,
            user=filler2,
            defaults={
                "status": "submitted",
                "started_at": timezone.now() - timedelta(minutes=30),
                "submitted_at": timezone.now() - timedelta(minutes=21),
                "duration_seconds": 540,
                "risk_flag": False,
                "device_fingerprint": "demo_device_2",
                "ip_hash": "demo_ip_hash_2",
            },
        )
        self._upsert_answer(r2, q1, value_text="宿舍")
        self._upsert_answer(r2, q2, value_json=["纸笔", "平板"])
        self._upsert_answer(r2, q3, value_text="增加插座会更好。")

        survey_b, qn_b, questions_b = surveys["survey_b"]
        qb1 = questions_b[0]
        r3, _ = Response.objects.update_or_create(
            survey=survey_b,
            questionnaire=qn_b,
            user=filler1,
            defaults={
                "status": "submitted",
                "started_at": timezone.now() - timedelta(minutes=8),
                "submitted_at": timezone.now() - timedelta(minutes=5),
                "duration_seconds": 180,
                "risk_flag": False,
                "device_fingerprint": "demo_device_1b",
                "ip_hash": "demo_ip_hash_1b",
            },
        )
        self._upsert_answer(r3, qb1, value_text="很满意")

        self._upsert_points_log(
            filler1,
            "reward",
            5,
            "[DEMO] 完成 [DEMO] 校园学习习惯调查",
            survey_a.id,
        )
        self._upsert_points_log(
            filler2,
            "reward",
            5,
            "[DEMO] 完成 [DEMO] 校园学习习惯调查",
            survey_a.id,
        )
        self._upsert_points_log(
            filler1,
            "reward",
            3,
            "[DEMO] 完成 [DEMO] 课程反馈快速问卷",
            survey_b.id,
        )

    @staticmethod
    def _sync_options(question, labels):
        existing = {
            opt.order_no: opt
            for opt in QuestionOption.objects.filter(question=question)
        }
        for idx, label in enumerate(labels, start=1):
            QuestionOption.objects.update_or_create(
                question=question,
                order_no=idx,
                defaults={
                    "label": label,
                    "value": label,
                    "is_other": False,
                },
            )
        QuestionOption.objects.filter(question=question, order_no__gt=len(labels)).delete()

    @staticmethod
    def _upsert_answer(response, question, value_text=None, value_json=None):
        Answer.objects.update_or_create(
            response=response,
            question=question,
            defaults={
                "value_text": value_text,
                "value_json": value_json,
            },
        )

    @staticmethod
    def _upsert_points_log(user, points_type, delta, reason, ref_id):
        PointsLog.objects.update_or_create(
            user=user,
            reason=reason,
            ref_type="survey",
            ref_id=ref_id,
            defaults={
                "points_type": points_type,
                "delta": delta,
            },
        )
