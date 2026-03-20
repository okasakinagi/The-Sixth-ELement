#!/usr/bin/env bash
# =============================================================================
# ops-cheatsheet.sh — 运维操作速查手册
# 本文件【不可顺序执行】，仅作命令参考。每段命令可独立复制到终端使用。
# 更新日期: 2026-03
# =============================================================================
#
# 目录
#   §1  进入容器 / Django Shell
#   §2  积分操作（增补 / 扣除 / 查流水）
#   §3  用户管理（查询 / 封禁 / 改信用分 / 改昵称）
#   §4  问卷管理（查询 / 强制关闭 / 暂停 / 恢复）
#   §5  举报处理（查看 / 标记已处理）
#   §6  角色与权限
#   §7  数据库辅助查询（SQL 直连）
#   §8  Django 管理命令
#   §9  日志与健康检查
#   §10 系统公告消息（站内信）
#
# =============================================================================


# =============================================================================
# §1  进入容器 / Django Shell
# =============================================================================

# ── 前置：所有命令在部署服务器宿主机上执行，working dir 是本仓库 deploy/ 目录
#    如 deploy/ 不是当前目录，请先 cd /path/to/project/deploy

# 查看正在运行的容器（确认 web 容器名称）
docker compose ps

# 进入 web 容器的交互式 Shell（用于执行后续所有 Python 命令）
docker compose exec web bash

# 在容器内启动 Django Shell（可直接写 ORM 代码）
#   注意：退出 Shell 用 exit() 或 Ctrl+D
docker compose exec web python Main.py shell

# 一次性执行单行 Python（不进入交互模式，适合脚本化操作）
#   格式：docker compose exec web python Main.py shell -c "<Python代码>"
docker compose exec web python Main.py shell -c "from core.models import AppUser; print(AppUser.objects.count())"


# =============================================================================
# §2  积分操作
# =============================================================================
# ⚠ 注意：所有积分操作必须同时更新 AppUser.points 和写入 PointsLog，
#          否则余额与流水对不上。请务必使用 transaction.atomic()。
#
# points_type 枚举值（写 PointsLog 时使用）：
#   "reward"       — 填写问卷获得奖励（系统自动）
#   "publish_cost" — 发布问卷扣费（系统自动）
#   "admin_adjust" — 管理员手动增补/扣除（运维场景使用此值）
#   "other"        — 其他来源
# =============================================================================

# ── §2.1  查询某用户当前积分余额
# 前置：需要知道用户邮箱，见 §7.1 查找用户邮箱
docker compose exec web python Main.py shell -c "
from core.models import AppUser
u = AppUser.objects.get(email='user@example.com')
print(f'昵称: {u.nickname}  |  积分: {u.points}  |  活动积分: {u.activity_points}')
"

# ── §2.2  给用户增加积分（带流水记录，事务安全）
# 参数说明：
#   email  — 用户注册邮箱（如何查找见 §7.1）
#   DELTA  — 正整数，增加的积分数量
#   REASON — 原因说明，显示在用户积分流水中（最多 200 字符）
docker compose exec web python Main.py shell -c "
from django.db import transaction
from core.models import AppUser, PointsLog
EMAIL  = 'user@example.com'   # ← 替换为目标用户邮箱
DELTA  = 50                    # ← 替换为增加的积分数（正数）
REASON = '管理员补偿：活动奖励' # ← 替换为原因
with transaction.atomic():
    u = AppUser.objects.select_for_update().get(email=EMAIL)
    before = u.points
    u.points += DELTA
    u.save(update_fields=['points'])
    PointsLog.objects.create(user=u, points_type='admin_adjust', delta=DELTA, reason=REASON)
print(f'操作完成：{before} → {u.points}（+{DELTA}）')
"

# ── §2.3  扣除用户积分（带流水记录，事务安全）
# 参数说明：
#   DELTA — 正整数，实际扣除数量（内部自动取负）
#   ⚠ 如果余额不足会抛出异常并回滚，不会造成负数
docker compose exec web python Main.py shell -c "
from django.db import transaction
from core.models import AppUser, PointsLog
EMAIL  = 'user@example.com'    # ← 替换为目标用户邮箱
DELTA  = 20                     # ← 替换为扣除数量（正数）
REASON = '管理员扣除：违规处罚' # ← 替换为原因
with transaction.atomic():
    u = AppUser.objects.select_for_update().get(email=EMAIL)
    if u.points < DELTA:
        raise ValueError(f'余额不足：当前 {u.points}，欲扣 {DELTA}')
    before = u.points
    u.points -= DELTA
    u.save(update_fields=['points'])
    PointsLog.objects.create(user=u, points_type='admin_adjust', delta=-DELTA, reason=REASON)
print(f'操作完成：{before} → {u.points}（-{DELTA}）')
"

# ── §2.4  查看某用户最近 20 条积分流水
docker compose exec web python Main.py shell -c "
from core.models import AppUser, PointsLog
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
logs = PointsLog.objects.filter(user=u).order_by('-created_at')[:20]
for l in logs:
    print(f'{l.created_at.strftime(\"%Y-%m-%d %H:%M\")}  {l.points_type:15s}  {l.delta:+d}  {l.reason}')
"

# ── §2.5  批量给多个用户增加积分（活动发奖场景）
# 前置：将目标用户邮箱整理到列表中
docker compose exec web python Main.py shell -c "
from django.db import transaction
from core.models import AppUser, PointsLog
EMAILS = [
    'user1@example.com',   # ← 替换为实际邮箱列表
    'user2@example.com',
]
DELTA  = 100
REASON = '春节活动奖励'
with transaction.atomic():
    for email in EMAILS:
        try:
            u = AppUser.objects.select_for_update().get(email=email)
            u.points += DELTA
            u.save(update_fields=['points'])
            PointsLog.objects.create(user=u, points_type='admin_adjust', delta=DELTA, reason=REASON)
            print(f'OK {email} +{DELTA}')
        except AppUser.DoesNotExist:
            print(f'SKIP 用户不存在: {email}')
"


# =============================================================================
# §3  用户管理
# =============================================================================
# AppUser.status 枚举值：
#   "normal"  — 正常
#   "banned"  — 封禁（前端登录/操作会被拒绝，需在业务层校验）
# =============================================================================

# ── §3.1  查询用户基本信息（按邮箱）
docker compose exec web python Main.py shell -c "
from core.models import AppUser
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
print(f'ID: {u.id}  昵称: {u.nickname}  积分: {u.points}  信用: {u.credit_score}  状态: {u.status}  注册: {u.created_at}')
"

# ── §3.2  搜索用户（昵称模糊匹配，不知道邮箱时使用）
docker compose exec web python Main.py shell -c "
from core.models import AppUser
users = AppUser.objects.filter(nickname__icontains='关键词')  # ← 替换关键词
for u in users:
    print(f'ID: {u.id}  昵称: {u.nickname}  邮箱: {u.email}  积分: {u.points}  状态: {u.status}')
"

# ── §3.3  封禁用户
docker compose exec web python Main.py shell -c "
from core.models import AppUser
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
u.status = 'banned'
u.save(update_fields=['status'])
print(f'已封禁: {u.nickname}')
"

# ── §3.4  解封用户
docker compose exec web python Main.py shell -c "
from core.models import AppUser
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
u.status = 'normal'
u.save(update_fields=['status'])
print(f'已解封: {u.nickname}')
"

# ── §3.5  修改用户信用分
# credit_score 初始值为 0，业务层逻辑根据实际需求决定范围
docker compose exec web python Main.py shell -c "
from core.models import AppUser
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
NEW_SCORE = 80                                       # ← 替换为目标分数
u.credit_score = NEW_SCORE
u.save(update_fields=['credit_score'])
print(f'信用分已更新: {u.nickname} → {u.credit_score}')
"

# ── §3.6  强制清除某用户的所有登录 Token（强制下线）
docker compose exec web python Main.py shell -c "
from core.models import AppUser, AuthToken
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
count, _ = AuthToken.objects.filter(user=u).delete()
print(f'已清除 {count} 个 Token，用户已强制下线: {u.nickname}')
"


# =============================================================================
# §4  问卷管理
# =============================================================================
# Survey.status 枚举值（内部存储）：
#   "draft"     — 草稿，未发布
#   "published" — 已发布，接受填写（任务大厅可见）
#   "paused"    — 暂停，不接受新填写（可恢复）
#   "closed"    — 已关闭（不可恢复）
#   "ended"     — 已结束
# =============================================================================

# ── §4.1  查询问卷基本信息（按 ID）
# 前置：需要知道 Survey ID（整数），见 §7.3 查找问卷 ID
docker compose exec web python Main.py shell -c "
from core.models import Survey
s = Survey.objects.get(id=123)  # ← 替换为问卷 ID（整数）
print(f'ID: {s.id}  标题: {s.title}  状态: {s.status}  发布者: {s.owner.nickname}  已完成: {s.completed}/{s.target}')
"

# ── §4.2  搜索问卷（标题关键词）
docker compose exec web python Main.py shell -c "
from core.models import Survey
surveys = Survey.objects.filter(title__icontains='关键词')  # ← 替换关键词
for s in surveys:
    print(f'ID: {s.id}  标题: {s.title}  状态: {s.status}  发布者: {s.owner.email}')
"

# ── §4.3  强制关闭问卷（不可逆）
docker compose exec web python Main.py shell -c "
from core.models import Survey
s = Survey.objects.get(id=123)  # ← 替换为问卷 ID
s.status = 'closed'
s.save(update_fields=['status'])
print(f'已关闭问卷: [{s.id}] {s.title}')
"

# ── §4.4  暂停问卷（可恢复）
docker compose exec web python Main.py shell -c "
from core.models import Survey
s = Survey.objects.get(id=123)  # ← 替换为问卷 ID
s.status = 'paused'
s.save(update_fields=['status'])
print(f'已暂停问卷: [{s.id}] {s.title}')
"

# ── §4.5  恢复被暂停的问卷
docker compose exec web python Main.py shell -c "
from core.models import Survey
s = Survey.objects.get(id=123)  # ← 替换为问卷 ID
if s.status != 'paused':
    print(f'当前状态不是 paused，而是 {s.status}，无法恢复')
else:
    s.status = 'published'
    s.save(update_fields=['status'])
    print(f'已恢复问卷: [{s.id}] {s.title}')
"

# ── §4.6  查看某用户发布的所有问卷
docker compose exec web python Main.py shell -c "
from core.models import AppUser, Survey
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
surveys = Survey.objects.filter(owner=u).order_by('-created_at')
for s in surveys:
    print(f'ID: {s.id}  {s.title}  {s.status}  {s.completed}/{s.target}  {s.created_at.date()}')
"


# =============================================================================
# §5  举报处理
# =============================================================================
# Report.status 枚举值：
#   "open"     — 待处理
#   "reviewed" — 已处理
# =============================================================================

# ── §5.1  查看所有待处理举报
docker compose exec web python Main.py shell -c "
from core.models import Report
reports = Report.objects.filter(status='open').order_by('-created_at')
for r in reports:
    print(f'ID: {r.id}  类型: {r.target_type}  目标ID: {r.target_id}  原因: {r.reason}  举报人: {r.reporter.email}  时间: {r.created_at.date()}')
"

# ── §5.2  标记举报为已处理
# 前置：需要管理员的 AppUser ID 作为 handled_by，见 §7.1 查询管理员 ID
docker compose exec web python Main.py shell -c "
from django.utils import timezone
from core.models import Report, AppUser
REPORT_ID  = 1                         # ← 替换为举报 ID
ADMIN_EMAIL = 'admin@example.com'      # ← 替换为执行操作的管理员邮箱
admin = AppUser.objects.get(email=ADMIN_EMAIL)
r = Report.objects.get(id=REPORT_ID)
r.status = 'reviewed'
r.handled_by = admin
r.handled_at = timezone.now()
r.save(update_fields=['status', 'handled_by', 'handled_at'])
print(f'举报 {REPORT_ID} 已标记处理，操作人: {admin.nickname}')
"


# =============================================================================
# §6  角色与权限
# =============================================================================
# Role 表存储角色定义，UserRole 表存储用户-角色关联。
# name 字段为字符串（如 "admin"，无固定枚举，由业务层约定）。
# =============================================================================

# ── §6.1  查看所有角色
docker compose exec web python Main.py shell -c "
from core.models import Role
for r in Role.objects.all():
    print(f'ID: {r.id}  名称: {r.name}  说明: {r.description}')
"

# ── §6.2  创建角色（首次部署后执行一次即可）
docker compose exec web python Main.py shell -c "
from core.models import Role
role, created = Role.objects.get_or_create(name='admin', defaults={'description': '系统管理员'})
print(f\"{'Created' if created else 'Already exists'}: Role id={role.id}\")
"

# ── §6.3  给某用户授予管理员角色
# 前置：需先确认 admin 角色已存在（§6.1 / §6.2）
docker compose exec web python Main.py shell -c "
from core.models import AppUser, Role, UserRole
u    = AppUser.objects.get(email='admin@example.com')  # ← 替换邮箱
role = Role.objects.get(name='admin')
ur, created = UserRole.objects.get_or_create(user=u, role=role)
print(f\"{'已授予' if created else '已存在'} 管理员角色: {u.nickname}\")
"

# ── §6.4  撤销某用户的管理员角色
docker compose exec web python Main.py shell -c "
from core.models import AppUser, Role, UserRole
u    = AppUser.objects.get(email='admin@example.com')  # ← 替换邮箱
role = Role.objects.get(name='admin')
deleted, _ = UserRole.objects.filter(user=u, role=role).delete()
print(f\"{'已撤销' if deleted else '该用户没有此角色'}: {u.nickname}\")
"

# ── §6.5  查看所有管理员用户
docker compose exec web python Main.py shell -c "
from core.models import Role, UserRole
role = Role.objects.get(name='admin')
for ur in UserRole.objects.filter(role=role).select_related('user'):
    print(f'ID: {ur.user.id}  昵称: {ur.user.nickname}  邮箱: {ur.user.email}')
"


# =============================================================================
# §7  数据库辅助查询（Django ORM）
# =============================================================================

# ── §7.1  按邮箱查找用户 ID（最常用前置操作）
docker compose exec web python Main.py shell -c "
from core.models import AppUser
u = AppUser.objects.get(email='user@example.com')  # ← 替换邮箱
print(u.id, u.nickname, u.email)
"

# ── §7.2  列出最近注册的 20 个用户
docker compose exec web python Main.py shell -c "
from core.models import AppUser
for u in AppUser.objects.order_by('-created_at')[:20]:
    print(f'{u.created_at.date()}  {u.email:40s}  {u.nickname}  积分:{u.points}')
"

# ── §7.3  列出最近发布的 20 个问卷（带发布者邮箱）
docker compose exec web python Main.py shell -c "
from core.models import Survey
for s in Survey.objects.select_related('owner').order_by('-created_at')[:20]:
    print(f'ID:{s.id:6d}  {s.status:10s}  {s.owner.email:35s}  {s.title[:40]}')
"

# ── §7.4  统计各状态问卷数量
docker compose exec web python Main.py shell -c "
from core.models import Survey
from django.db.models import Count
for row in Survey.objects.values('status').annotate(cnt=Count('id')).order_by('status'):
    print(f'{row[\"status\"]:12s}: {row[\"cnt\"]}')
"

# ── §7.5  统计总用户数、今日注册数
docker compose exec web python Main.py shell -c "
from django.utils import timezone
from core.models import AppUser
today = timezone.now().date()
print(f'总用户: {AppUser.objects.count()}  今日注册: {AppUser.objects.filter(created_at__date=today).count()}')
"

# ── §7.6  直连 MySQL 容器执行 SQL（用于复杂查询，不推荐 DML）
# 前置：需要 .env 中的 DB_USER / DB_PASSWORD / DB_NAME
docker compose exec db mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}"
# 进入 MySQL 后示例查询：
#   SELECT id, nickname, email, points FROM core_appuser ORDER BY created_at DESC LIMIT 20;
#   SELECT points_type, COUNT(*), SUM(delta) FROM core_pointslog GROUP BY points_type;
#   SHOW TABLES;


# =============================================================================
# §8  Django 管理命令
# =============================================================================

# ── §8.1  填充演示数据（仅限开发/测试环境）
docker compose exec web python Main.py seed_demo_data

# ── §8.2  数据库迁移（部署新版本后执行）
docker compose exec web python Main.py migrate

# ── §8.3  查看所有可用 manage 命令
docker compose exec web python Main.py help

# ── §8.4  检查项目配置是否有问题
docker compose exec web python Main.py check


# =============================================================================
# §9  日志与健康检查
# =============================================================================

# ── §9.1  查看 web 容器最新日志（持续跟踪）
docker compose logs -f web

# ── §9.2  查看最近 100 行日志（不跟踪）
docker compose logs --tail=100 web

# ── §9.3  查看数据库容器日志
docker compose logs --tail=50 db

# ── §9.4  健康检查接口（返回 200 ok 表示服务正常）
curl -f http://127.0.0.1:8000/healthz && echo "OK" || echo "FAIL"

# ── §9.5  重启 web 容器（不停数据库）
docker compose restart web

# ── §9.6  完全停止并重建 web 容器（发布新镜像后使用）
#   先 build 新镜像，再 up（-d 后台运行）
docker build -f docker/backend.Dockerfile -t backend:latest .
docker compose up -d --no-deps web

# ── §9.7  查看容器资源占用（CPU / 内存）
docker stats --no-stream


# =============================================================================
# §10  系统公告消息（站内信）
# =============================================================================
# 说明：写入 core.models.Message，message_type='system'，sender=None。
# 建议：公告文案控制在 500 字以内，标题清晰，避免重复群发。

# ── §10.1  给单个用户发送系统公告（按邮箱）
docker compose exec web python Main.py shell -c "
from core.models import AppUser, Message
EMAIL = 'user@example.com'          # ← 替换目标用户邮箱
TITLE = '系统公告'                    # ← 替换标题
CONTENT = '系统将于今晚 23:00 进行维护，预计 15 分钟。'  # ← 替换正文
u = AppUser.objects.get(email=EMAIL)
msg = Message.objects.create(
    user=u,
    sender=None,
    type='system',
    message_type='system',
    title=TITLE,
    content=CONTENT,
    status='unread',
    ref_type='announcement',
)
print(f'已发送给 {u.email}，message_id={msg.id}')
"

# ── §10.2  给多个用户发送系统公告（按邮箱列表，批量）
docker compose exec web python Main.py shell -c "
from core.models import AppUser, Message
EMAILS = [
    'user1@example.com',   # ← 替换邮箱
    'user2@example.com',
]
TITLE = '系统公告'                     # ← 替换标题
CONTENT = '问卷服务升级已完成，欢迎继续使用。'  # ← 替换正文
users = list(AppUser.objects.filter(email__in=EMAILS))
email_set = {u.email for u in users}
missing = [e for e in EMAILS if e not in email_set]
if missing:
    print('以下邮箱不存在，将跳过:')
    for e in missing:
        print(' -', e)

msgs = [
    Message(
        user=u,
        sender=None,
        type='system',
        message_type='system',
        title=TITLE,
        content=CONTENT,
        status='unread',
        ref_type='announcement',
    )
    for u in users
]
if msgs:
    Message.objects.bulk_create(msgs)
print(f'发送完成：成功 {len(msgs)} 人，跳过 {len(missing)} 人')
"

# ── §10.3  给全体用户发送系统公告（谨慎使用）
# ⚠ 生产环境建议在业务低峰执行；用户量大时会创建大量消息记录。
docker compose exec web python Main.py shell -c "
from core.models import AppUser, Message
TITLE = '系统公告'  # ← 替换标题
CONTENT = '平台新版本已上线，欢迎体验。'  # ← 替换正文

users = AppUser.objects.all().only('id')
batch_size = 1000
buffer = []
total = 0

for u in users.iterator(chunk_size=batch_size):
    buffer.append(
        Message(
            user_id=u.id,
            sender=None,
            type='system',
            message_type='system',
            title=TITLE,
            content=CONTENT,
            status='unread',
            ref_type='announcement',
        )
    )
    if len(buffer) >= batch_size:
        Message.objects.bulk_create(buffer, batch_size=batch_size)
        total += len(buffer)
        buffer = []

if buffer:
    Message.objects.bulk_create(buffer, batch_size=batch_size)
    total += len(buffer)

print(f'全体公告发送完成，共 {total} 条消息')
"
