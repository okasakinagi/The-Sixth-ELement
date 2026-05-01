import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module.survey_app.settings')
import django
django.setup()

from core.models import RiskRule

print("开始更新风控规则动作（仅记录，不自动处罚）...")
print("=" * 60)

rules_to_update = RiskRule.objects.filter(rule_code__in=[
    'short_duration_30s',
    'short_duration_10s',
    'time_anomaly_night',
])

for rule in rules_to_update:
    old_actions = rule.actions
    rule.actions = ['log']
    rule.description = rule.description.replace('视为异常行为', '仅记录供管理员参考')
    rule.description = rule.description.replace('视为高风险行为', '仅记录供管理员参考')
    rule.description = rule.description.replace('视为可疑行为', '仅记录供管理员参考')
    rule.save()
    print(f"更新规则: {rule.rule_name}")
    print(f"  旧动作: {old_actions}")
    print(f"  新动作: {rule.actions}")
    print()

print("=" * 60)
print("更新完成！")