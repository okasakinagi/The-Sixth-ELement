from core.models import AppUser, Survey, Questionnaire
from core.services.similarity_service import SimilarityService
import json

# create owner and user
owner, _ = AppUser.objects.get_or_create(email='owner@example.com', defaults={'nickname':'owner'})
user, _ = AppUser.objects.get_or_create(email='tester@example.com', defaults={'nickname':'tester'})

# create survey if not exists
survey, created = Survey.objects.get_or_create(title='Test Survey', owner=owner, defaults={'status':'published'})
if created:
    Questionnaire.objects.create(survey=survey, version=1, status='published', title=survey.title)
    try:
        survey.active_questionnaire = survey.questionnaire_set.first()
        survey.save(update_fields=['active_questionnaire'])
    except Exception:
        pass

print('owner_id=', owner.id, 'user_id=', user.id, 'survey_id=', survey.id)

# generate vectors (best-effort)
try:
    sv = SimilarityService.generate_and_store_vector('survey', str(survey.id))
except Exception as e:
    sv = None
    print('survey vector generation error:', e)

try:
    uv = SimilarityService.generate_and_store_vector('user', str(user.id))
except Exception as e:
    uv = None
    print('user vector generation error:', e)

print('survey_vector_len=', len(sv) if sv else None, 'user_vector_len=', len(uv) if uv else None)

# rank candidate surveys (new architecture: user-vec x survey-vec cosine)
try:
    from core.models import Survey as _Survey
    all_ids = list(_Survey.objects.values_list('id', flat=True))[:20]
    recs = SimilarityService.rank_candidate_surveys_for_user(str(user.id), all_ids)
    print('rank:', json.dumps(recs))
except Exception as e:
    print('rank error:', e)

# compute cosine
try:
    res = SimilarityService.get_or_compute_daily_cosine(str(user.id), str(survey.id))
    print('compute:', res)
except Exception as e:
    print('compute error:', e)

print('done')
