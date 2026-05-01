import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module.survey_app.settings')
import django
django.setup()

from core.models import AppUser, Survey, RiskEvent, RiskRule
from core.services.risk_engine_service import RiskEngine

print("=" * 60)
print("测试风控规则引擎")
print("=" * 60)

print("\n1. 当前启用的规则：")
enabled_rules = RiskRule.get_enabled_rules()
for rule in enabled_rules:
    print(f"   - {rule.rule_name} (类型: {rule.event_type}, 阈值: {rule.conditions})")

print("\n2. 创建测试数据...")
test_user = AppUser.objects.first()
test_survey = Survey.objects.first()

if not test_user:
    print("   错误：没有找到测试用户")
    exit(1)

print(f"   测试用户: {test_user.nickname} (ID: {test_user.id})")
if test_survey:
    print(f"   测试问卷: {test_survey.title} (ID: {test_survey.id})")
else:
    print("   注意：没有找到问卷，使用 None")

print("\n3. 测试场景1：正常时长（60秒）")
RiskEvent.objects.filter(user=test_user).delete()
triggered = RiskEngine.evaluate_submission(
    user=test_user,
    survey=test_survey,
    duration_seconds=60,
    answers=['A', 'B', 'C', 'A', 'B', 'C']
)
print(f"   触发规则数: {len(triggered)}")
print(f"   预期：应该触发固定答案规则（如果有连续3个相同）")

print("\n4. 测试场景2：短时长（5秒）")
triggered = RiskEngine.evaluate_submission(
    user=test_user,
    survey=test_survey,
    duration_seconds=5,
    answers=['A', 'B', 'C', 'A', 'B', 'C']
)
print(f"   触发规则数: {len(triggered)}")
for rule in triggered:
    print(f"   - {rule.rule_name}")
print(f"   预期：应该触发 short_duration_30s 和 short_duration_10s")

print("\n5. 测试场景3：固定答案（连续5个A）")
triggered = RiskEngine.evaluate_submission(
    user=test_user,
    survey=test_survey,
    duration_seconds=30,
    answers=['A', 'A', 'A', 'A', 'A']
)
print(f"   触发规则数: {len(triggered)}")
for rule in triggered:
    print(f"   - {rule.rule_name}")
print(f"   预期：应该触发 fixed_answer_detection")

print("\n6. 验证数据库中的风控事件：")
events = RiskEvent.objects.filter(user=test_user).order_by('-created_at')
print(f"   共 {events.count()} 条风控事件")
for event in events[:5]:
    print(f"   - [{event.event_type}] {event.severity} - {event.created_at}")

print("\n7. 统计验证：")
short_count = RiskEvent.objects.filter(event_type="short_duration").count()
fixed_count = RiskEvent.objects.filter(event_type="fixed_answer").count()
print(f"   短时长事件总数: {short_count}")
print(f"   固定答案事件总数: {fixed_count}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)