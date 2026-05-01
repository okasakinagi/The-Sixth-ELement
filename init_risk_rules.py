import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module.survey_app.settings')
import django
django.setup()

from core.services.risk_engine_service import RiskEngine

print("开始初始化默认风控规则...")
print("=" * 60)

created_count = RiskEngine.initialize_default_rules()

print("=" * 60)
print(f"完成！共创建 {created_count} 条风控规则")

from core.models import RiskRule
print("\n当前所有风控规则：")
for rule in RiskRule.objects.all().order_by("priority"):
    status = "✅" if rule.enabled else "❌"
    print(f"  {status} {rule.rule_name} ({rule.rule_code}) - 优先级: {rule.priority}")