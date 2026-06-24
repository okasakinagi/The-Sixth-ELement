from collections import defaultdict
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from math import exp, sqrt
import hashlib
import random
import json
import os
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

from core.models import (
    IDVector,
    SurveyUserSimilarity,
    Survey,
    AppUser,
    Question,
    SurveyTag,
    UserTag,
    UserTagWeight,
    Response,
)


class SimilarityManager:
    _TAG_WEIGHT_DECAY_LAMBDA = 0.05

    # 大学生场景兴趣关联映射：用于补齐“语义相关但标签不完全相同”的情况。
    _INTEREST_RELATION_MAP = {
        "python": {
            "java": 0.7,
            "c++": 0.7,
            "数据分析": 0.8,
            "大模型开发": 0.9,
            "编程竞赛": 0.8,
            "人工智能": 0.9,
            "机器学习": 0.9,
        },
        "java": {
            "python": 0.7,
            "c++": 0.7,
            "编程竞赛": 0.8,
            "软件工程": 0.8,
        },
        "c++": {
            "python": 0.7,
            "java": 0.7,
            "编程竞赛": 0.9,
            "算法": 0.9,
        },
        "编程竞赛": {
            "python": 0.8,
            "java": 0.8,
            "c++": 0.9,
            "算法": 0.9,
            "数据结构": 0.9,
        },
        "心理学": {
            "心理健康": 0.9,
            "消费行为": 0.6,
            "社会调查": 0.7,
            "大学生情绪": 0.9,
        },
        "考研": {
            "考公": 0.6,
            "专业课": 0.8,
            "研究生生活": 0.9,
            "就业": 0.7,
        },
    }

    @staticmethod
    def _is_same_day(dt1, dt2):
        return dt1.date() == dt2.date()

    @staticmethod
    def get_similarity_today(survey_id, user_id):
        now = timezone.now()
        row = (
            SurveyUserSimilarity.objects.filter(survey_id=survey_id, user_id=user_id)
            .order_by("-created_at")
            .first()
        )
        if row and SimilarityManager._is_same_day(row.created_at, now):
            return row
        return None

    @staticmethod
    def fetch_vector(ref_type, ref_id):
        node = IDVector.objects.filter(ref_type=ref_type, ref_id=str(ref_id)).first()
        if not node:
            return None
        return node.get_vector()

    @staticmethod
    def save_vector(ref_type, ref_id, vec):
        node, _ = IDVector.objects.get_or_create(ref_type=ref_type, ref_id=str(ref_id))
        node.set_vector(vec)
        node.save()
        return node

    @staticmethod
    def invalidate_vector(ref_type, ref_id):
        """删除缓存向量，下次推荐请求时将重新生成。"""
        IDVector.objects.filter(ref_type=ref_type, ref_id=str(ref_id)).delete()

    @staticmethod
    def compute_cosine(vec_a, vec_b):
        if not vec_a or not vec_b:
            return None
        # ensure same length
        if len(vec_a) != len(vec_b):
            # truncate to shorter
            n = min(len(vec_a), len(vec_b))
            vec_a = vec_a[:n]
            vec_b = vec_b[:n]
        dot = sum(x * y for x, y in zip(vec_a, vec_b))
        norm_a = sqrt(sum(x * x for x in vec_a))
        norm_b = sqrt(sum(y * y for y in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    @transaction.atomic
    def store_similarity(survey_id, user_id, cosine):
        survey = Survey.objects.filter(id=survey_id).first()
        user = AppUser.objects.filter(id=user_id).first()
        obj, _ = SurveyUserSimilarity.objects.update_or_create(
            survey=survey, user=user, defaults={"cosine": cosine}
        )
        return obj

    @staticmethod
    def deterministic_text_to_vector(text, dim=100):
        """A simple deterministic placeholder vectorizer."""
        # Use sha256 to seed RNG deterministically
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:8], "big")
        rnd = random.Random(seed)
        # generate floats in [-1,1]
        vec = [rnd.uniform(-1.0, 1.0) for _ in range(dim)]
        return vec

    @staticmethod
    def _embedding_env():
        api_key = os.getenv("EMBEDDING_API_KEY", "").strip()
        base_url = os.getenv("EMBEDDING_BASE_URL", "").strip()
        model = os.getenv("EMBEDDING_MODEL", "").strip()

        return {
            "api_key": api_key,
            "base_url": SimilarityManager._normalize_embedding_base_url(base_url),
            "model": model,
        }

    @staticmethod
    def _normalize_embedding_base_url(base_url):
        raw = str(base_url or "").strip()
        if not raw:
            return ""
        normalized = raw.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return f"{normalized[:-len('/chat/completions')]}/embeddings"
        if normalized.endswith("/v1"):
            return f"{normalized}/embeddings"
        if "/embeddings" in normalized:
            return normalized
        return normalized

    @staticmethod
    def encode_text(text, dim=100):
        """Encode text to vector.

        Behavior:
        - If EMBEDDING_API_KEY/BASE_URL/MODEL are configured, call OpenAI-compatible
          embeddings endpoint.
        - Otherwise fall back to deterministic local vectorizer.
        """
        cfg = SimilarityManager._embedding_env()
        if not cfg["api_key"] or not cfg["base_url"] or not cfg["model"]:
            return SimilarityManager.deterministic_text_to_vector(text, dim=dim)

        payload = json.dumps({"model": cfg["model"], "input": text}).encode("utf-8")
        req = urlrequest.Request(
            cfg["base_url"],
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg['api_key']}",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                emb = data.get("data") or []
                if emb and isinstance(emb[0], dict) and emb[0].get("embedding"):
                    vec = emb[0]["embedding"]
                    return [float(v) for v in vec]
        except (urlerror.URLError, ValueError, KeyError, TimeoutError):
            pass

        return SimilarityManager.deterministic_text_to_vector(text, dim=dim)

    # 标签类型 → 中文标签名映射，用于生成自然语言描述
    _TAG_TYPE_LABEL = {
        "interest": "兴趣爱好",
        "school": "学校",
        "major": "专业",
        "gender": "性别",
        "age": "年龄",
        "grade": "年级",
        "college": "学院",
        "mbti": "MBTI",
        "organization": "参与组织",
        "consumption": "消费偏好",
        "career": "职业方向",
        "skill": "技能特长",
        "survey_type": "偏好问卷类型",
        "status": "状态",
    }

    @staticmethod
    def generate_placeholder_string(ref_type, ref_id):
        """返回用于向量化的描述性文本。

        - user: 按标签类型分组、按权重降序排列的自然语言描述；高权重标签重复出现以加强语义权重
        - survey: 标题 + 描述 + 标签 + 前5道题目标题
        - other: 返回空串
        """
        if ref_type == "user":
            rows = list(
                UserTagWeight.objects.filter(user_id=ref_id, weight__gt=0)
                .select_related("tag")
                .order_by("-weight")
            )
            if not rows:
                # 回退：用户有标签但无权重记录
                tags = list(
                    UserTag.objects.filter(user_id=ref_id)
                    .select_related("tag")
                    .order_by("tag_id")
                )
                tag_names = [t.tag.name for t in tags]
                if not tag_names:
                    return ""
                return "用户兴趣标签：" + " ".join(tag_names)

            type_groups = defaultdict(list)
            type_order = []
            for row in rows:
                t = row.tag.type
                if t not in type_order:
                    type_order.append(t)
                type_groups[t].append((row.tag.name, float(row.weight)))

            parts = []
            for t in type_order:
                group = type_groups[t]
                label = SimilarityManager._TAG_TYPE_LABEL.get(t, t)
                tag_parts = []
                for name, weight in group:
                    # 高权重标签重复出现，加强该方向的语义信号
                    repeat = 3 if weight >= 4.0 else (2 if weight >= 2.0 else 1)
                    tag_parts.extend([name] * repeat)
                parts.append(f"{label}：{' '.join(tag_parts)}")
            return "；".join(parts)

        if ref_type == "survey":
            try:
                survey_obj = Survey.objects.select_related("active_questionnaire").get(
                    id=int(ref_id)
                )
            except (Survey.DoesNotExist, ValueError):
                return ""

            parts = [f"问卷标题：{survey_obj.title}"]
            if survey_obj.description:
                parts.append(f"问卷描述：{survey_obj.description}")

            tag_rows = (
                SurveyTag.objects.filter(survey_id=ref_id)
                .select_related("tag")
                .order_by("tag_id")
            )
            tag_names = [r.tag.name for r in tag_rows]
            if tag_names:
                parts.append(f"分类标签：{' '.join(tag_names)}")

            questionnaire = survey_obj.active_questionnaire
            if questionnaire:
                questions = Question.objects.filter(
                    questionnaire=questionnaire
                ).order_by("order_no")[:5]
                q_titles = [q.title for q in questions if q.title]
                if q_titles:
                    parts.append(f"题目摘要：{'；'.join(q_titles)}")

            return "。".join(parts)

        return ""

    @staticmethod
    def generate_and_store_vector(ref_type, ref_id, dim=100, force=False):
        """生成并持久化向量。

        缓存策略：向量存在时直接复用（依赖 invalidate_vector 显式失效）。
        force=True 时强制重新生成并覆盖缓存。
        """
        node = IDVector.objects.filter(ref_type=ref_type, ref_id=str(ref_id)).first()
        if node and node.vector and not force:
            return node.get_vector()

        text = SimilarityManager.generate_placeholder_string(ref_type, ref_id)
        vec = SimilarityManager.encode_text(text, dim=dim)
        return SimilarityManager.save_vector(ref_type, ref_id, vec).get_vector()

    @staticmethod
    def _normalize_tag_name(name):
        if name is None:
            return ""
        return str(name).strip().lower()

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))

    @staticmethod
    def _build_user_tag_weight_map(user_id):
        now = timezone.now()
        rows = list(
            UserTagWeight.objects.filter(user_id=user_id)
            .select_related("tag")
            .order_by("-updated_at")
        )
        weight_map = {}
        for row in rows:
            tag_name = SimilarityManager._normalize_tag_name(row.tag.name)
            if not tag_name:
                continue
            day_diff = 0.0
            if row.updated_at:
                day_diff = max((now - row.updated_at).total_seconds() / 86400.0, 0.0)
            decay_factor = exp(-SimilarityManager._TAG_WEIGHT_DECAY_LAMBDA * day_diff)
            decayed_weight = float(row.weight or 0.0) * float(decay_factor)
            weight_map[tag_name] = weight_map.get(tag_name, 0.0) + float(decayed_weight)

        # 兼容老数据：如果没有权重记录，回退到用户标签并赋予基础权重。
        if weight_map:
            return weight_map

        fallback_rows = list(
            UserTag.objects.filter(user_id=user_id)
            .select_related("tag")
            .order_by("tag_id")
        )
        for row in fallback_rows:
            tag_name = SimilarityManager._normalize_tag_name(row.tag.name)
            if not tag_name:
                continue
            weight_map[tag_name] = 1.0
        return weight_map

    @staticmethod
    def _build_survey_tag_map(survey_ids):
        mapping = defaultdict(set)
        rows = SurveyTag.objects.filter(survey_id__in=survey_ids).select_related("tag")
        for row in rows:
            tag_name = SimilarityManager._normalize_tag_name(row.tag.name)
            if not tag_name:
                continue
            mapping[int(row.survey_id)].add(tag_name)
        return mapping

    @staticmethod
    def _compute_tag_hard_match_score(user_weight_map, survey_tag_set):
        if not user_weight_map:
            return 0.0, 0.0
        if not survey_tag_set:
            return 0.0, 0.0

        positive_budget = sum(max(0.0, float(w)) for w in user_weight_map.values())
        if positive_budget <= 0:
            return 0.0, 0.0

        raw_score = 0.0
        for user_tag, user_weight in user_weight_map.items():
            if abs(float(user_weight)) < 1e-9:
                continue

            # 同一用户标签在当前问卷标签集合里只取“最强匹配”防止重复加成。
            best_match = 0.0
            if user_tag in survey_tag_set:
                best_match = 1.0
            else:
                related = SimilarityManager._INTEREST_RELATION_MAP.get(user_tag, {})
                for survey_tag in survey_tag_set:
                    best_match = max(best_match, float(related.get(survey_tag, 0.0)))

            raw_score += float(user_weight) * best_match

        normalized = SimilarityManager._clamp(
            (raw_score / positive_budget) * 100.0, 0.0, 100.0
        )
        return raw_score, normalized

    @staticmethod
    def _normalize_question_type(qtype):
        raw = str(qtype or "").strip().lower()
        if raw == "single":
            return "single"
        if raw == "multi":
            return "multi"
        if raw in {"text", "multi-text", "open", "textarea"}:
            return "open"
        if raw in {"scale", "rating", "likert"}:
            return "scale"
        return "single"

    @staticmethod
    def _percentile(values, p):
        if not values:
            return 0.0
        arr = sorted(values)
        if len(arr) == 1:
            return float(arr[0])
        idx = (len(arr) - 1) * p
        lo = int(idx)
        hi = min(lo + 1, len(arr) - 1)
        frac = idx - lo
        return float(arr[lo] * (1 - frac) + arr[hi] * frac)

    @staticmethod
    def _get_question_profiles(questionnaire_ids):
        profile = {
            int(qid): {
                "total": 0,
                "type_counts": {"single": 0, "multi": 0, "scale": 0, "open": 0},
            }
            for qid in questionnaire_ids
        }
        if not questionnaire_ids:
            return profile

        total_rows = (
            Question.objects.filter(questionnaire_id__in=questionnaire_ids)
            .values("questionnaire_id")
            .annotate(cnt=Count("id"))
        )
        for row in total_rows:
            qid = int(row["questionnaire_id"])
            profile.setdefault(
                qid,
                {
                    "total": 0,
                    "type_counts": {"single": 0, "multi": 0, "scale": 0, "open": 0},
                },
            )
            profile[qid]["total"] = int(row["cnt"])

        type_rows = (
            Question.objects.filter(questionnaire_id__in=questionnaire_ids)
            .values("questionnaire_id", "type")
            .annotate(cnt=Count("id"))
        )
        for row in type_rows:
            qid = int(row["questionnaire_id"])
            norm_type = SimilarityManager._normalize_question_type(row["type"])
            profile.setdefault(
                qid,
                {
                    "total": 0,
                    "type_counts": {"single": 0, "multi": 0, "scale": 0, "open": 0},
                },
            )
            profile[qid]["type_counts"][norm_type] += int(row["cnt"])
        return profile

    @staticmethod
    def _build_user_behavior_signals(user_id):
        now = timezone.now()
        day_ago = now - timedelta(hours=24)
        month_ago = now - timedelta(days=30)
        quarter_ago = now - timedelta(days=90)

        filled_ids = set(
            Response.objects.filter(
                user_id=user_id, submitted_at__isnull=False
            ).values_list("survey_id", flat=True)
        )

        dislike_rows = UserTagWeight.objects.filter(
            user_id=user_id,
            weight__lte=0.01,
            updated_at__gte=month_ago,
        ).select_related("tag")
        hard_dislike_tags = {
            SimilarityManager._normalize_tag_name(row.tag.name)
            for row in dislike_rows
            if SimilarityManager._normalize_tag_name(row.tag.name)
        }

        quit_rows = list(
            Response.objects.filter(user_id=user_id)
            .filter(Q(status="in_progress") | Q(submitted_at__isnull=True))
            .values("survey_id", "created_at")
        )
        quit_survey_ids = [
            int(row["survey_id"]) for row in quit_rows if row.get("survey_id")
        ]
        quit_tag_map = SimilarityManager._build_survey_tag_map(quit_survey_ids)

        quit_tags = set()
        blocked_tags_24h = set()
        quit_count_24h_by_tag = defaultdict(int)
        for row in quit_rows:
            sid = int(row["survey_id"])
            tags = quit_tag_map.get(sid, set())
            if row.get("created_at") and row["created_at"] >= quarter_ago:
                quit_tags.update(tags)
            if row.get("created_at") and row["created_at"] >= day_ago:
                for tag in tags:
                    quit_count_24h_by_tag[tag] += 1
        for tag, cnt in quit_count_24h_by_tag.items():
            if cnt > 2:
                blocked_tags_24h.add(tag)

        submitted_rows = list(
            Response.objects.filter(
                user_id=user_id,
                submitted_at__isnull=False,
                duration_seconds__isnull=False,
                duration_seconds__gt=0,
            )
            .filter(submitted_at__gte=quarter_ago)
            .values("survey_id", "questionnaire_id", "duration_seconds", "submitted_at")
        )
        qids = [
            int(row["questionnaire_id"])
            for row in submitted_rows
            if row.get("questionnaire_id")
        ]
        q_profile_map = SimilarityManager._get_question_profiles(qids)

        submitted_survey_ids = [
            int(row["survey_id"]) for row in submitted_rows if row.get("survey_id")
        ]
        submitted_tag_map = SimilarityManager._build_survey_tag_map(
            submitted_survey_ids
        )

        slow_tags = set()
        domain_fill_count_24h = defaultdict(int)
        for row in submitted_rows:
            sid = int(row["survey_id"])
            qid = int(row["questionnaire_id"])
            duration = float(row["duration_seconds"] or 0)
            q_total = int(q_profile_map.get(qid, {}).get("total", 0))
            if q_total <= 0:
                continue
            per_question = duration / q_total
            tags = submitted_tag_map.get(sid, set())
            if per_question > 30.0:
                slow_tags.update(tags)
            if row.get("submitted_at") and row["submitted_at"] >= day_ago:
                for tag in tags:
                    domain_fill_count_24h[tag] += 1

        return {
            "filled_survey_ids": filled_ids,
            "hard_dislike_tags": hard_dislike_tags,
            "quit_tags": quit_tags,
            "slow_tags": slow_tags,
            "blocked_tags_24h": blocked_tags_24h,
            "domain_fill_count_24h": domain_fill_count_24h,
        }

    @staticmethod
    def _build_user_efficiency_profile(user_id):
        rows = list(
            Response.objects.filter(
                user_id=user_id,
                submitted_at__isnull=False,
                duration_seconds__isnull=False,
                duration_seconds__gt=0,
            ).values("survey_id", "questionnaire_id", "duration_seconds")
        )
        if not rows:
            return {
                "tolerate_time": 10.0,
                "tolerate_num": 15.0,
                "type_ratio": {
                    "single": 0.35,
                    "multi": 0.25,
                    "scale": 0.2,
                    "open": 0.2,
                },
                "domain_proficiency": {},
                "overall_proficiency": 0.5,
            }

        questionnaire_ids = [
            int(row["questionnaire_id"]) for row in rows if row.get("questionnaire_id")
        ]
        q_profile_map = SimilarityManager._get_question_profiles(questionnaire_ids)

        survey_ids = [int(row["survey_id"]) for row in rows if row.get("survey_id")]
        survey_tag_map = SimilarityManager._build_survey_tag_map(survey_ids)

        per_question_times = []
        question_nums = []
        user_type_counts = defaultdict(int)
        domain_time_acc = defaultdict(list)

        for row in rows:
            qid = int(row["questionnaire_id"])
            sid = int(row["survey_id"])
            duration = float(row["duration_seconds"] or 0)

            q_profile = q_profile_map.get(qid, {})
            total_q = int(q_profile.get("total", 0))
            if total_q <= 0:
                continue

            per_question = duration / total_q
            per_question_times.append(per_question)
            question_nums.append(total_q)

            for qtype, cnt in q_profile.get("type_counts", {}).items():
                user_type_counts[qtype] += int(cnt)

            for tag in survey_tag_map.get(sid, set()):
                domain_time_acc[tag].append(per_question)

        tolerate_time = (
            sum(per_question_times) / len(per_question_times)
            if per_question_times
            else 10.0
        )
        tolerate_num = (
            SimilarityManager._percentile(question_nums, 0.9) if question_nums else 15.0
        )

        type_sum = sum(user_type_counts.values())
        if type_sum > 0:
            type_ratio = {
                qtype: float(user_type_counts.get(qtype, 0)) / float(type_sum)
                for qtype in ("single", "multi", "scale", "open")
            }
        else:
            type_ratio = {"single": 0.35, "multi": 0.25, "scale": 0.2, "open": 0.2}

        raw_proficiency = {}
        for tag, times in domain_time_acc.items():
            if not times:
                continue
            avg_t = sum(times) / len(times)
            if avg_t <= 0:
                continue
            raw_proficiency[tag] = 1.0 / avg_t

        if raw_proficiency:
            max_raw = max(raw_proficiency.values()) or 1.0
            domain_proficiency = {
                tag: SimilarityManager._clamp(val / max_raw, 0.0, 1.0)
                for tag, val in raw_proficiency.items()
            }
            overall = sum(domain_proficiency.values()) / len(domain_proficiency)
        else:
            domain_proficiency = {}
            overall = 0.5

        return {
            "tolerate_time": float(tolerate_time),
            "tolerate_num": float(tolerate_num),
            "type_ratio": type_ratio,
            "domain_proficiency": domain_proficiency,
            "overall_proficiency": float(overall),
        }

    @staticmethod
    def _estimate_domain_level(difficulty, survey_tag_set):
        hard_keywords = {"算法", "编程竞赛", "大模型开发", "机器学习", "考研", "专业课"}
        light_keywords = {"校园生活", "心理健康", "大学生情绪", "娱乐", "社交"}

        if int(difficulty or 0) >= 4:
            return 0.8
        if int(difficulty or 0) <= 2:
            return 0.3
        if any(tag in hard_keywords for tag in survey_tag_set):
            return 0.8
        if any(tag in light_keywords for tag in survey_tag_set):
            return 0.3
        return 0.5

    @staticmethod
    def _build_survey_efficiency_profile_map(survey_ids, survey_tag_map):
        profile_map = {}
        if not survey_ids:
            return profile_map

        surveys = Survey.objects.filter(id__in=survey_ids).select_related(
            "active_questionnaire"
        )
        qid_map = {}
        survey_meta = {}
        questionnaire_ids = []
        for survey in surveys:
            qid = int(survey.active_questionnaire_id or 0)
            qid_map[int(survey.id)] = qid
            if qid > 0:
                questionnaire_ids.append(qid)
            survey_meta[int(survey.id)] = {
                "difficulty": int(survey.difficulty or 3),
            }

        q_profile_map = SimilarityManager._get_question_profiles(questionnaire_ids)

        for sid in survey_ids:
            sid = int(sid)
            qid = int(qid_map.get(sid, 0))
            q_profile = q_profile_map.get(
                qid,
                {
                    "total": 0,
                    "type_counts": {"single": 0, "multi": 0, "scale": 0, "open": 0},
                },
            )
            total_q = int(q_profile.get("total", 0))
            if total_q <= 0:
                total_q = 1

            type_counts = q_profile.get("type_counts", {})
            weighted_seconds = (
                int(type_counts.get("single", 0)) * 5
                + int(type_counts.get("multi", 0)) * 8
                + int(type_counts.get("scale", 0)) * 6
                + int(type_counts.get("open", 0)) * 30
            )
            pre_time = float(weighted_seconds) / float(total_q)

            type_ratio = {
                qtype: float(int(type_counts.get(qtype, 0))) / float(total_q)
                for qtype in ("single", "multi", "scale", "open")
            }

            tags = survey_tag_map.get(sid, set())
            primary_tag = sorted(tags)[0] if tags else ""
            domain_level = SimilarityManager._estimate_domain_level(
                survey_meta.get(sid, {}).get("difficulty", 3),
                tags,
            )

            profile_map[sid] = {
                "pre_time": pre_time,
                "question_num": float(total_q),
                "type_ratio": type_ratio,
                "domain_level": float(domain_level),
                "primary_tag": primary_tag,
            }

        return profile_map

    @staticmethod
    def _compute_efficiency_score(user_profile, survey_profile, domain_fill_count_24h):
        user_tolerate_time = float(user_profile.get("tolerate_time", 10.0) or 10.0)
        user_tolerate_num = float(user_profile.get("tolerate_num", 15.0) or 15.0)
        user_type_ratio = user_profile.get("type_ratio") or {}
        user_domain_proficiency = user_profile.get("domain_proficiency") or {}
        user_overall_proficiency = float(
            user_profile.get("overall_proficiency", 0.5) or 0.5
        )

        ques_pre_time = float(survey_profile.get("pre_time", 8.0) or 8.0)
        ques_question_num = float(survey_profile.get("question_num", 10.0) or 10.0)
        ques_type_ratio = survey_profile.get("type_ratio") or {}
        ques_domain_level = float(survey_profile.get("domain_level", 0.5) or 0.5)
        ques_primary_tag = survey_profile.get("primary_tag") or ""

        if ques_pre_time <= user_tolerate_time:
            time_score = 100.0
        else:
            time_score = 100.0 * (user_tolerate_time / max(ques_pre_time, 1e-9))
        time_score = SimilarityManager._clamp(time_score, 0.0, 100.0)

        if ques_question_num <= user_tolerate_num:
            num_score = 100.0
        else:
            num_score = 100.0 * (user_tolerate_num / max(ques_question_num, 1e-9))
        num_score = SimilarityManager._clamp(num_score, 0.0, 100.0)

        type_score = 100.0
        for qtype in ("single", "multi", "scale", "open"):
            q_ratio = float(ques_type_ratio.get(qtype, 0.0) or 0.0)
            u_ratio = float(user_type_ratio.get(qtype, 0.0) or 0.0)
            punish = 2.0 if qtype == "open" else 1.0
            type_score -= abs(q_ratio - u_ratio) * 100.0 * punish
        type_score = SimilarityManager._clamp(type_score, 0.0, 100.0)

        user_domain_level = float(
            user_domain_proficiency.get(ques_primary_tag, user_overall_proficiency)
        )
        if ques_domain_level <= user_domain_level:
            pro_score = 100.0
        else:
            pro_score = 100.0 * (user_domain_level / max(ques_domain_level, 1e-9))
        pro_score = SimilarityManager._clamp(pro_score, 0.0, 100.0)

        efficiency_score = (
            time_score * 0.4 + num_score * 0.3 + type_score * 0.2 + pro_score * 0.1
        )

        fatigue_count = int(domain_fill_count_24h.get(ques_primary_tag, 0))
        tired_punish = 1.0 / (1.0 + 0.2 * float(max(fatigue_count, 0)))
        efficiency_score *= tired_punish

        return SimilarityManager._clamp(efficiency_score, 0.0, 100.0)

    @staticmethod
    def rank_surveys_for_user(user_id, survey_ids, exclude_ids=None, dim=100):
        """对候选问卷按“标签硬匹配 + 语义匹配”融合分排序。

        流程：
        1. 获取/生成用户整体描述向量。
        2. 批量查询已缓存的问卷向量；对未缓存问卷生成描述字符串并嵌入。
        3. 计算标签硬匹配分与语义余弦分，得到兴趣匹配分。
        4. 以最终分（当前阶段等于兴趣分）排序，输出兼容字段。
        """
        if not survey_ids:
            return []

        user_id = int(user_id)
        exclude_set = {int(x) for x in (exclude_ids or [])}
        cleaned_sids = [int(sid) for sid in survey_ids if int(sid) not in exclude_set]
        if not cleaned_sids:
            return []

        # 0. 行为信号：用于前置硬过滤 + 行为惩罚。
        behavior = SimilarityManager._build_user_behavior_signals(user_id)

        # 1. 获取/生成用户整体向量
        user_vec = SimilarityManager.generate_and_store_vector(
            "user", str(user_id), dim=dim, force=False
        )

        # 1.1 用户标签权重（用于标签硬匹配）
        user_weight_map = SimilarityManager._build_user_tag_weight_map(user_id)

        # 1.2 问卷标签缓存（批量）
        survey_tag_map = SimilarityManager._build_survey_tag_map(cleaned_sids)

        # 1.3 前置硬过滤：减少无效候选与后续计算。
        filtered_sids = []
        for sid in cleaned_sids:
            tags = survey_tag_map.get(sid, set())
            if sid in behavior["filled_survey_ids"]:
                continue
            if tags & behavior["hard_dislike_tags"]:
                continue
            if tags & behavior["blocked_tags_24h"]:
                continue
            filtered_sids.append(sid)

        if not filtered_sids:
            return []

        # 1.4 效率画像：用户侧一次计算，问卷侧批量计算。
        user_efficiency = SimilarityManager._build_user_efficiency_profile(user_id)
        survey_efficiency_map = SimilarityManager._build_survey_efficiency_profile_map(
            filtered_sids,
            survey_tag_map,
        )

        # 2. 批量查询已缓存的问卷向量
        str_sids = [str(sid) for sid in filtered_sids]
        existing_nodes = IDVector.objects.filter(ref_type="survey", ref_id__in=str_sids)
        vec_by_survey = {
            int(node.ref_id): node.get_vector()
            for node in existing_nodes
            if node.get_vector()
        }

        # 对尚未缓存的问卷生成描述字符串并嵌入
        uncached = [sid for sid in filtered_sids if sid not in vec_by_survey]
        for sid in uncached:
            text = SimilarityManager.generate_placeholder_string("survey", str(sid))
            if text:
                vec = SimilarityManager.encode_text(text, dim=dim)
                SimilarityManager.save_vector("survey", str(sid), vec)
                vec_by_survey[sid] = vec

        # 3. 计算余弦相似度并排序
        ranked = []
        for sid in filtered_sids:
            survey_tag_set = survey_tag_map.get(sid, set())
            _raw_tag_score, tag_score_norm = (
                SimilarityManager._compute_tag_hard_match_score(
                    user_weight_map,
                    survey_tag_set,
                )
            )

            survey_vec = vec_by_survey.get(sid)
            cosine = 0.0
            if user_vec is not None and survey_vec is not None:
                cosine = float(
                    SimilarityManager.compute_cosine(user_vec, survey_vec) or 0.0
                )

            # 语义分使用 0-100 量纲；余弦负值按 0 处理，避免反向拉低稳定性。
            cosine_01 = SimilarityManager._clamp(cosine, 0.0, 1.0)
            semantic_score = cosine_01 * 100.0

            # 阶段2：兴趣匹配分 = 标签硬匹配(60%) + 语义匹配(40%)
            interest_score = (tag_score_norm * 0.6) + (semantic_score * 0.4)

            # 阶段3：效率适配分
            survey_efficiency = survey_efficiency_map.get(
                sid,
                {
                    "pre_time": 8.0,
                    "question_num": 10.0,
                    "type_ratio": {
                        "single": 0.35,
                        "multi": 0.25,
                        "scale": 0.2,
                        "open": 0.2,
                    },
                    "domain_level": 0.5,
                    "primary_tag": "",
                },
            )
            efficiency_score = SimilarityManager._compute_efficiency_score(
                user_efficiency,
                survey_efficiency,
                behavior["domain_fill_count_24h"],
            )

            # 阶段4：行为惩罚因子
            penalty_factor = 1.0
            if survey_tag_set & behavior["quit_tags"]:
                penalty_factor *= 0.5
            if survey_tag_set & behavior["slow_tags"]:
                penalty_factor *= 0.7

            # 阶段1内核：最终分 = 兴趣匹配分 * 效率适配分 * 行为惩罚因子
            final_score = interest_score * (efficiency_score / 100.0) * penalty_factor

            if tag_score_norm >= 60:
                reason = "标签硬匹配优先"
            elif semantic_score >= 60:
                reason = "基于内容语义匹配"
            else:
                reason = "标签与语义综合匹配"

            if survey_vec is None:
                reason = "问卷向量不可用，已按标签匹配兜底"
            elif user_vec is None:
                reason = "用户向量不可用，已按标签匹配兜底"

            ranked.append(
                {
                    "survey_id": sid,
                    "score": 0.0,
                    "final_score": SimilarityManager._clamp(final_score, 0.0, 100.0),
                    "interest_score": SimilarityManager._clamp(
                        interest_score, 0.0, 100.0
                    ),
                    "efficiency_score": efficiency_score,
                    "penalty_factor": penalty_factor,
                    "tag_score": SimilarityManager._clamp(tag_score_norm, 0.0, 100.0),
                    "semantic_score": SimilarityManager._clamp(
                        semantic_score, 0.0, 100.0
                    ),
                    "reason": reason,
                }
            )

        # 排序主语义仍以 final_score 为准；随后计算兼容旧前端阈值的 score（0~1）。
        ranked.sort(key=lambda x: x["final_score"], reverse=True)

        if ranked:
            total = len(ranked)
            min_final = min(item["final_score"] for item in ranked)
            max_final = max(item["final_score"] for item in ranked)
            spread = max_final - min_final

            for idx, item in enumerate(ranked):
                absolute_component = SimilarityManager._clamp(
                    float(item.get("final_score", 0.0)) / 100.0,
                    0.0,
                    1.0,
                )

                if total <= 1:
                    rank_component = absolute_component
                else:
                    rank_component = 1.0 - (float(idx) / float(total - 1))

                if spread > 1e-9:
                    relative_component = (
                        float(item.get("final_score", 0.0)) - min_final
                    ) / spread
                else:
                    # 当本批候选分布非常接近时，使用相对名次拉开显示层次，避免“全部低匹配”。
                    relative_component = rank_component

                compat_score = SimilarityManager._clamp(
                    (relative_component * 0.55)
                    + (rank_component * 0.25)
                    + (absolute_component * 0.20),
                    0.0,
                    1.0,
                )
                item["score"] = compat_score

        return ranked
