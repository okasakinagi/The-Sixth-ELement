import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module.survey_app.settings')
import django
django.setup()

from core.models import AppUser

print('检查用户状态分布:')
statuses = AppUser.objects.values('status').annotate(count=django.db.models.Count('id'))
for s in statuses:
    print(f'  status="{s["status"]}": {s["count"]} 人')

print('\n所有用户状态:')
for u in AppUser.objects.all():
    print(f'  ID={u.id}, nickname={u.nickname}, status="{u.status}"')