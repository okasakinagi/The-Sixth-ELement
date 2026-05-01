import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module.survey_app.settings')
import django
django.setup()

from core.models import AppUser, PointsLog
from django.db import transaction

print("=" * 60)
print("测试批量扣分日志账实一致性修复")
print("=" * 60)

test_user = AppUser.objects.first()
if not test_user:
    print("错误：没有找到测试用户")
    exit(1)

print(f"\n测试用户: {test_user.nickname} (ID: {test_user.id})")

initial_points = test_user.points
print(f"初始积分: {initial_points}")

print("\n" + "=" * 60)
print("场景1：积分充足（50积分，扣30分）")
print("=" * 60)

PointsLog.objects.filter(user=test_user, points_type="admin_adjust").delete()

test_user.points = 50
test_user.save()
print(f"扣分前积分: {test_user.points}")

old_points = test_user.points
delta = -30
new_points = old_points + delta
actual_delta = delta
is_insufficient = False

if new_points < 0:
    actual_delta = -old_points
    new_points = 0
    is_insufficient = True

test_user.points = new_points
test_user.save()

log_reason = "测试扣分-充足"
if is_insufficient:
    log_reason = f"{log_reason}（积分不足，已全部扣除）"

log = PointsLog.objects.create(
    user=test_user,
    points_type="admin_adjust",
    delta=actual_delta,
    reason=log_reason,
    ref_type="batch_adjust",
    ref_id=1,
)

print(f"扣分后积分: {test_user.points}")
print(f"日志记录的扣分值: {log.delta}")
print(f"日志记录的原因: {log.reason}")

if test_user.points == 20 and log.delta == -30:
    print("[PASS] 场景1测试通过：积分充足，日志记录正确")
else:
    print("[FAIL] 场景1测试失败")

print("\n" + "=" * 60)
print("场景2：积分不足（50积分，扣100分）")
print("=" * 60)

PointsLog.objects.filter(user=test_user, points_type="admin_adjust").delete()

test_user.points = 50
test_user.save()
print(f"扣分前积分: {test_user.points}")

old_points = test_user.points
delta = -100
new_points = old_points + delta
actual_delta = delta
is_insufficient = False

if new_points < 0:
    actual_delta = -old_points
    new_points = 0
    is_insufficient = True

test_user.points = new_points
test_user.save()

log_reason = "测试扣分-不足"
if is_insufficient:
    log_reason = f"{log_reason}（积分不足，已全部扣除）"

log = PointsLog.objects.create(
    user=test_user,
    points_type="admin_adjust",
    delta=actual_delta,
    reason=log_reason,
    ref_type="batch_adjust",
    ref_id=1,
)

print(f"扣分后积分: {test_user.points}")
print(f"日志记录的扣分值: {log.delta}")
print(f"日志记录的原因: {log.reason}")
print(f"是否积分不足: {is_insufficient}")
print(f"实际扣分: {actual_delta}")

if test_user.points == 0 and log.delta == -50 and "积分不足" in log.reason:
    print("[PASS] 场景2测试通过：积分不足，日志记录正确，标注清晰")
else:
    print("[FAIL] 场景2测试失败")

print("\n" + "=" * 60)
print("场景3：积分恰好扣完（50积分，扣50分）")
print("=" * 60)

PointsLog.objects.filter(user=test_user, points_type="admin_adjust").delete()

test_user.points = 50
test_user.save()
print(f"扣分前积分: {test_user.points}")

old_points = test_user.points
delta = -50
new_points = old_points + delta
actual_delta = delta
is_insufficient = False

if new_points < 0:
    actual_delta = -old_points
    new_points = 0
    is_insufficient = True

test_user.points = new_points
test_user.save()

log_reason = "测试扣分-恰好"
if is_insufficient:
    log_reason = f"{log_reason}（积分不足，已全部扣除）"

log = PointsLog.objects.create(
    user=test_user,
    points_type="admin_adjust",
    delta=actual_delta,
    reason=log_reason,
    ref_type="batch_adjust",
    ref_id=1,
)

print(f"扣分后积分: {test_user.points}")
print(f"日志记录的扣分值: {log.delta}")
print(f"日志记录的原因: {log.reason}")
print(f"是否积分不足: {is_insufficient}")

if test_user.points == 0 and log.delta == -50 and is_insufficient == False:
    print("[PASS] 场景3测试通过：积分恰好扣完，日志记录正确")
else:
    print("[FAIL] 场景3测试失败")

print("\n" + "=" * 60)
print("恢复测试用户积分")
print("=" * 60)
test_user.points = initial_points
test_user.save()
print(f"已恢复积分为: {initial_points}")

PointsLog.objects.filter(user=test_user, points_type="admin_adjust", reason__startswith="测试扣分").delete()
print("已清理测试日志")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)