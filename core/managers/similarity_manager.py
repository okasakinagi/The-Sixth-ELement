from collections import defaultdict
from django.db import transaction
from django.utils import timezone
from math import sqrt
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
)


class SimilarityManager:
    _AI_CONFIG_CACHE = None

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
        """A simple deterministic placeholder vectorizer.

        TODO: replace this with real embedding model/service.
        """
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

        # Fallback to deploy/ai_config.json when env vars are not fully provided.
        if not (api_key and base_url and model):
            file_cfg = SimilarityManager._load_ai_config()
            api_key = api_key or file_cfg.get("api_key", "")
            base_url = base_url or file_cfg.get("base_url", "")
            model = model or file_cfg.get("model", "")

        return {
            "api_key": api_key.strip(),
            "base_url": SimilarityManager._normalize_embedding_base_url(base_url),
            "model": model.strip(),
        }

    @staticmethod
    def _load_ai_config():
        if SimilarityManager._AI_CONFIG_CACHE is not None:
            return SimilarityManager._AI_CONFIG_CACHE
        try:
            project_root = Path(__file__).resolve().parents[2]
            config_path = project_root / "deploy" / "ai_config.json"
            if not config_path.exists():
                SimilarityManager._AI_CONFIG_CACHE = {}
                return {}
            with config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                SimilarityManager._AI_CONFIG_CACHE = {}
                return {}

            # Backward compatibility: old flat fields remain supported.
            flat = {
                "api_key": str(data.get("api_key") or "").strip(),
                "base_url": str(data.get("base_url") or "").strip(),
                "model": str(data.get("model") or "").strip(),
            }
            embedding_raw = data.get("embedding")
            if isinstance(embedding_raw, dict):
                cfg = {
                    "api_key": str(
                        embedding_raw.get("api_key") or flat["api_key"]
                    ).strip(),
                    "base_url": str(
                        embedding_raw.get("base_url") or flat["base_url"]
                    ).strip(),
                    "model": str(embedding_raw.get("model") or flat["model"]).strip(),
                }
            else:
                cfg = flat
            SimilarityManager._AI_CONFIG_CACHE = cfg
            return cfg
        except Exception:
            SimilarityManager._AI_CONFIG_CACHE = {}
            return {}

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
    def rank_surveys_for_user(user_id, survey_ids, exclude_ids=None, dim=100):
        """对候选问卷按用户-问卷整体向量余弦相似度排序推荐。

        流程：
        1. 获取/生成用户整体描述向量。
        2. 批量查询已缓存的问卷向量；对未缓存问卷生成描述字符串并嵌入。
        3. 计算余弦相似度，按分数降序返回。
        """
        if not survey_ids:
            return []

        exclude_set = {int(x) for x in (exclude_ids or [])}
        cleaned_sids = [int(sid) for sid in survey_ids if int(sid) not in exclude_set]
        if not cleaned_sids:
            return []

        # 1. 获取/生成用户整体向量
        user_vec = SimilarityManager.generate_and_store_vector(
            "user", str(user_id), dim=dim, force=False
        )
        if user_vec is None:
            return [
                {"survey_id": sid, "score": 0.0, "reason": "用户向量不可用"}
                for sid in cleaned_sids
            ]

        # 2. 批量查询已缓存的问卷向量
        str_sids = [str(sid) for sid in cleaned_sids]
        existing_nodes = IDVector.objects.filter(ref_type="survey", ref_id__in=str_sids)
        vec_by_survey = {
            int(node.ref_id): node.get_vector()
            for node in existing_nodes
            if node.get_vector()
        }

        # 对尚未缓存的问卷生成描述字符串并嵌入
        uncached = [sid for sid in cleaned_sids if sid not in vec_by_survey]
        for sid in uncached:
            text = SimilarityManager.generate_placeholder_string("survey", str(sid))
            if text:
                vec = SimilarityManager.encode_text(text, dim=dim)
                SimilarityManager.save_vector("survey", str(sid), vec)
                vec_by_survey[sid] = vec

        # 3. 计算余弦相似度并排序
        ranked = []
        for sid in cleaned_sids:
            survey_vec = vec_by_survey.get(sid)
            if survey_vec is None:
                ranked.append(
                    {"survey_id": sid, "score": 0.0, "reason": "问卷向量不可用"}
                )
                continue
            cosine = SimilarityManager.compute_cosine(user_vec, survey_vec)
            score = float(cosine or 0.0)
            ranked.append(
                {"survey_id": sid, "score": score, "reason": "基于内容语义匹配"}
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
