from django.utils import timezone
from django.db import transaction
from math import sqrt
import hashlib
import random

from core.models import IDVector, SurveyUserSimilarity, Survey, AppUser


class SimilarityManager:
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
        obj, created = SurveyUserSimilarity.objects.update_or_create(
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
    def generate_placeholder_string(ref_type, ref_id):
        """返回用于向量化的占位字符串（当前实现返回空串，TODO 可替换为真实文本生成逻辑）。"""
        return ""

    @staticmethod
    def generate_and_store_vector(ref_type, ref_id, dim=100):
        """检查数据库：若已存在（用户且为当天，或问卷任意时间）则直接返回现有向量；否则生成字符串、转向量并保存。

        返回 Python 列表形式的向量。
        """
        now = timezone.now()
        node = IDVector.objects.filter(ref_type=ref_type, ref_id=str(ref_id)).first()
        if node and node.vector:
            # 已有向量，用户需检查是否为同一天
            if ref_type == "user":
                if node.created_at and node.created_at.date() == now.date():
                    return node.get_vector()
            else:
                return node.get_vector()

        # 生成用于编码的文本（当前占位）
        text = SimilarityManager.generate_placeholder_string(ref_type, ref_id)
        vec = SimilarityManager.deterministic_text_to_vector(text, dim=dim)
        # 保存并返回
        return SimilarityManager.save_vector(ref_type, ref_id, vec).get_vector()
