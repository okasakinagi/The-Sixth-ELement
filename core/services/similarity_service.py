from core.managers.similarity_manager import SimilarityManager
from core.models import Survey
from django.conf import settings


class SimilarityService:
    @staticmethod
    def get_or_compute_daily_cosine(user_id, survey_id):
        # Use existing manager behavior (which now applies a 30-minute TTL for user vectors)
        user_vec = SimilarityManager.generate_and_store_vector(
            "user", str(user_id), dim=100, force=False
        )
        survey_vec = SimilarityManager.generate_and_store_vector(
            "survey", str(survey_id), dim=100, force=False
        )
        if user_vec is None or survey_vec is None:
            return {
                "error": "missing_vector",
                "message": "user or survey vector not found",
            }

        cosine = SimilarityManager.compute_cosine(user_vec, survey_vec)
        obj = SimilarityManager.store_similarity(survey_id, user_id, cosine)
        return {"cosine": float(cosine), "cached": False, "created_at": obj.created_at}

    @staticmethod
    def encode_and_store(ref_type, ref_id, text, dim=100):
        vec = SimilarityManager.encode_text(text, dim=dim)
        SimilarityManager.save_vector(ref_type, ref_id, vec)
        return vec

    @staticmethod
    def generate_placeholder(ref_type, ref_id):
        return SimilarityManager.generate_placeholder_string(ref_type, ref_id)

    @staticmethod
    def generate_and_store_vector(ref_type, ref_id, dim=100):
        # For the public/internal generate endpoint: force recompute for user type, keep survey behavior
        if ref_type == "user":
            return SimilarityManager.generate_and_store_vector(
                ref_type, ref_id, dim=dim, force=True
            )
        return SimilarityManager.generate_and_store_vector(
            ref_type, ref_id, dim=dim, force=False
        )

    @staticmethod
    def rank_candidate_surveys_for_user(
        user_id, candidate_survey_ids, exclude_ids=None
    ):
        return SimilarityManager.rank_surveys_for_user(
            user_id=user_id,
            survey_ids=[int(x) for x in (candidate_survey_ids or [])],
            exclude_ids=[int(x) for x in (exclude_ids or [])],
            dim=100,
        )

    @staticmethod
    def recommend_surveys_for_user(user_id, k, exclude_ids=None):
        # mode switch: 'personalized' (default) uses similarity ranking; 'random' returns pure random
        mode = getattr(settings, "RECOMMENDATION_MODE", "personalized")
        if mode == "random":
            qs = Survey.objects.all()
            if exclude_ids:
                qs = qs.exclude(id__in=[int(x) for x in exclude_ids])
            qs = list(qs.order_by("?")[: max(int(k), 0)])
            return [{"id": str(s.id), "title": s.title, "cosine": None} for s in qs]

        survey_ids = list(Survey.objects.values_list("id", flat=True))
        ranked = SimilarityService.rank_candidate_surveys_for_user(
            user_id=user_id,
            candidate_survey_ids=survey_ids,
            exclude_ids=exclude_ids,
        )
        top = ranked[: max(int(k), 0)]

        surveys = {
            s.id: s
            for s in Survey.objects.filter(id__in=[item["survey_id"] for item in top])
        }
        items = []
        for item in top:
            survey = surveys.get(item["survey_id"])
            if not survey:
                continue
            items.append(
                {
                    "id": str(survey.id),
                    "title": survey.title,
                    "cosine": float(item["score"]),
                    "reason": item.get("reason", ""),
                }
            )
        return items
