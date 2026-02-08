from core.managers.similarity_manager import SimilarityManager
from django.utils import timezone


class SimilarityService:
    @staticmethod
    def get_or_compute_daily_cosine(user_id, survey_id):
        # check existing today
        row = SimilarityManager.get_similarity_today(survey_id, user_id)
        if row:
            return {
                "cosine": float(row.cosine),
                "cached": True,
                "created_at": row.created_at,
            }

        # fetch vectors
        user_vec = SimilarityManager.fetch_vector("user", str(user_id))
        survey_vec = SimilarityManager.fetch_vector("survey", str(survey_id))
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
        # placeholder deterministic encoding, TODO: replace with real embedding
        vec = SimilarityManager.deterministic_text_to_vector(text, dim=dim)
        SimilarityManager.save_vector(ref_type, ref_id, vec)
        return vec

    @staticmethod
    def generate_placeholder(ref_type, ref_id):
        # currently returns empty string; kept as service wrapper
        return SimilarityManager.generate_placeholder_string(ref_type, ref_id)

    @staticmethod
    def generate_and_store_vector(ref_type, ref_id, dim=100):
        return SimilarityManager.generate_and_store_vector(ref_type, ref_id, dim=dim)

    @staticmethod
    def recommend_surveys_for_user(user_id, k):
        # sample 10*k random surveys
        sample_n = max(10 * k, k)
        surveys = list(Survey.objects.order_by("?")[:sample_n])
        results = []
        # ensure user vector exists (may generate)
        user_vec = SimilarityManager.fetch_vector("user", str(user_id))
        if user_vec is None:
            SimilarityManager.generate_and_store_vector("user", str(user_id))
            user_vec = SimilarityManager.fetch_vector("user", str(user_id))

        for s in surveys:
            sid = s.id
            # try to get cached similarity (today)
            row = SimilarityManager.get_similarity_today(sid, user_id)
            if row:
                cosine = float(row.cosine)
            else:
                survey_vec = SimilarityManager.fetch_vector("survey", str(sid))
                if survey_vec is None:
                    # generate survey vector
                    SimilarityManager.generate_and_store_vector("survey", str(sid))
                    survey_vec = SimilarityManager.fetch_vector("survey", str(sid))
                cosine = SimilarityManager.compute_cosine(user_vec, survey_vec)
                # store for future
                SimilarityManager.store_similarity(sid, user_id, cosine)
            results.append((s, cosine if cosine is not None else -1.0))

        # sort descending by cosine (closest to 1)
        results.sort(key=lambda x: x[1], reverse=True)
        top = results[:k]
        return [
            {"id": str(item[0].id), "title": item[0].title, "cosine": item[1]}
            for item in top
        ]
