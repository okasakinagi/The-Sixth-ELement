from core.models import UserBehaviorLog


class UserBehaviorLogService:
    @staticmethod
    def log_event(user_id, event_type, survey_id=None, scene="task_list", meta=None):
        if not user_id or not event_type:
            return
        payload = meta if isinstance(meta, dict) else {}
        try:
            UserBehaviorLog.objects.create(
                user_id=user_id,
                survey_id=survey_id,
                event_type=event_type,
                scene=scene,
                meta_json=payload,
            )
        except Exception:
            # 埋点失败不影响主链路。
            return

    @staticmethod
    def log_impressions(user_id, survey_ids, scene="task_list", meta=None):
        if not user_id:
            return
        if not survey_ids:
            return

        cleaned_ids = []
        seen = set()
        for sid in survey_ids:
            try:
                value = int(sid)
            except (TypeError, ValueError):
                continue
            if value <= 0 or value in seen:
                continue
            seen.add(value)
            cleaned_ids.append(value)

        if not cleaned_ids:
            return

        payload = meta if isinstance(meta, dict) else {}
        try:
            rows = [
                UserBehaviorLog(
                    user_id=user_id,
                    survey_id=sid,
                    event_type="impression",
                    scene=scene,
                    meta_json=payload,
                )
                for sid in cleaned_ids
            ]
            UserBehaviorLog.objects.bulk_create(rows, batch_size=200)
        except Exception:
            # 埋点失败不影响主链路。
            return
