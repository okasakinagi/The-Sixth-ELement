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
        # If a user vector was updated, refresh any cached SurveyUserSimilarity rows for this user
        if ref_type == "user":
            try:
                user_vec = node.get_vector()
                rows = SurveyUserSimilarity.objects.filter(user__id=ref_id)
                for row in rows:
                    survey_vec = SimilarityManager.fetch_vector("survey", str(row.survey.id))
                    if survey_vec is None:
                        continue
                    cosine = SimilarityManager.compute_cosine(user_vec, survey_vec)
                    row.cosine = float(cosine) if cosine is not None else 0.0
                    row.save(update_fields=["cosine"])
            except Exception:
                # non-fatal: keep vector saved even if cache refresh fails
                pass
        return node

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
                    "api_key": str(embedding_raw.get("api_key") or flat["api_key"]).strip(),
                    "base_url": str(embedding_raw.get("base_url") or flat["base_url"]).strip(),
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

    @staticmethod
    def generate_placeholder_string(ref_type, ref_id):
        """返回用于向量化的文本。

        - user: 拼接该用户 tag 与权重
        - survey: 拼接该问卷 tag
        - other: 返回空串
        """
        if ref_type == "user":
            rows = (
                UserTagWeight.objects.filter(user_id=ref_id)
                .select_related("tag")
                .order_by("tag_id")
            )
            if rows:
                return " ".join([f"{r.tag.name}:{float(r.weight):.3f}" for r in rows])
            tags = UserTag.objects.filter(user_id=ref_id).select_related("tag").order_by("tag_id")
            return " ".join([t.tag.name for t in tags])

        if ref_type == "survey":
            rows = SurveyTag.objects.filter(survey_id=ref_id).select_related("tag").order_by("tag_id")
            return " ".join([r.tag.name for r in rows])

        return ""

    @staticmethod
    def generate_and_store_vector(ref_type, ref_id, dim=100, force=False):
        """生成并持久化向量。"""
        now = timezone.now()
        node = IDVector.objects.filter(ref_type=ref_type, ref_id=str(ref_id)).first()
        if node and node.vector and not force:
            # 已有向量，用户向量按 TTL 缓存（30 分钟）；survey/tag 向量直接复用
            if ref_type == "user":
                if node.created_at and (now - node.created_at).total_seconds() <= 30 * 60:
                    return node.get_vector()
            else:
                return node.get_vector()

        text = SimilarityManager.generate_placeholder_string(ref_type, ref_id)
        vec = SimilarityManager.encode_text(text, dim=dim)
        return SimilarityManager.save_vector(ref_type, ref_id, vec).get_vector()

    @staticmethod
    def _get_or_create_tag_vectors(tag_rows, dim=100):
        """Load vectors for tag rows; generate and cache missing ones."""
        tag_ids = [str(row.tag_id) for row in tag_rows]
        if not tag_ids:
            return {}

        existing = IDVector.objects.filter(ref_type="tag", ref_id__in=tag_ids)
        vec_by_tag = {int(node.ref_id): node.get_vector() for node in existing if node.get_vector()}

        for row in tag_rows:
            tid = int(row.tag_id)
            if tid in vec_by_tag:
                continue
            vec = SimilarityManager.encode_text(row.tag.name, dim=dim)
            SimilarityManager.save_vector("tag", str(tid), vec)
            vec_by_tag[tid] = vec
        return vec_by_tag

    @staticmethod
    def _user_tag_rows(user_id):
        rows = list(
            UserTagWeight.objects.filter(user_id=user_id)
            .select_related("tag")
            .order_by("tag_id")
        )
        if rows:
            return [r for r in rows if float(r.weight) > 0.0]

        # fallback: user has tags but no weight record yet
        tags = list(UserTag.objects.filter(user_id=user_id).select_related("tag").order_by("tag_id"))
        class _Tmp:
            def __init__(self, tag):
                self.tag = tag
                self.tag_id = tag.id
                self.weight = 1.0

        return [_Tmp(t.tag) for t in tags]

    @staticmethod
    def rank_surveys_for_user(user_id, survey_ids, exclude_ids=None, dim=100):
        """Rank surveys by user-tag/survey-tag semantic matching score.

        Score design:
        - For each survey tag, find the best matched user tag cosine.
        - Multiply by normalized user tag weight.
        - Final score = average of best matches across survey tags.
        """
        if not survey_ids:
            return []

        exclude_set = {int(x) for x in (exclude_ids or [])}
        cleaned_sids = [int(sid) for sid in survey_ids if int(sid) not in exclude_set]
        if not cleaned_sids:
            return []

        user_rows = SimilarityManager._user_tag_rows(user_id)
        if not user_rows:
            return [{"survey_id": sid, "score": 0.0, "reason": "标签信息不足"} for sid in cleaned_sids]

        survey_rows = list(
            SurveyTag.objects.filter(survey_id__in=cleaned_sids)
            .select_related("tag")
            .order_by("survey_id", "tag_id")
        )

        # Build vector cache for all involved tags
        all_rows = list(user_rows) + survey_rows
        vec_by_tag = SimilarityManager._get_or_create_tag_vectors(all_rows, dim=dim)

        user_weight_max = max(float(r.weight) for r in user_rows) or 1.0
        user_rows_scored = []
        for row in user_rows:
            vec = vec_by_tag.get(int(row.tag_id))
            if not vec:
                continue
            user_rows_scored.append(
                {
                    "tag_id": int(row.tag_id),
                    "tag_name": row.tag.name,
                    "weight": float(row.weight) / user_weight_max,
                    "vec": vec,
                }
            )

        if not user_rows_scored:
            return [{"survey_id": sid, "score": 0.0, "reason": "标签向量缺失"} for sid in cleaned_sids]

        survey_tags = {}
        for row in survey_rows:
            sid = int(row.survey_id)
            survey_tags.setdefault(sid, []).append(row)

        ranked = []
        for sid in cleaned_sids:
            rows = survey_tags.get(sid, [])
            if not rows:
                ranked.append({"survey_id": sid, "score": 0.0, "reason": "问卷暂无标签"})
                continue

            best_scores = []
            best_pairs = []
            for srow in rows:
                svec = vec_by_tag.get(int(srow.tag_id))
                if not svec:
                    continue
                best = None
                best_pair = None
                for u in user_rows_scored:
                    cosine = SimilarityManager.compute_cosine(svec, u["vec"])
                    cosine = float(cosine or 0.0)
                    weighted = cosine * u["weight"]
                    if best is None or weighted > best:
                        best = weighted
                        best_pair = (srow.tag.name, u["tag_name"])
                if best is not None:
                    best_scores.append(best)
                    if best_pair:
                        best_pairs.append(best_pair)

            if not best_scores:
                ranked.append({"survey_id": sid, "score": 0.0, "reason": "标签向量缺失"})
                continue

            score = float(sum(best_scores) / len(best_scores))
            reason = ""
            if best_pairs:
                s_tag, u_tag = best_pairs[0]
                reason = f"问卷标签“{s_tag}”与你的“{u_tag}”匹配"

            ranked.append({"survey_id": sid, "score": score, "reason": reason})

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
