import hashlib
import json
import secrets
<<<<<<< Updated upstream
from datetime import datetime, time, timedelta, timezone as dt_timezone
=======
import random
import string
from datetime import datetime, time, timedelta
>>>>>>> Stashed changes

from django.conf import settings as django_settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import (
    AppUser,
    AuthCredential,
    AuthToken,
<<<<<<< Updated upstream
    PasswordResetCode,
=======
    PasswordReset,
>>>>>>> Stashed changes
    PointsLog,
    Questionnaire,
    Report,
    Response,
    Survey,
    Tag,
    UserTag,
    UserTagWeight,
)
from core.managers.similarity_manager import SimilarityManager

# 权重参数
WEIGHT_MANUAL = 1.0
WEIGHT_INCREMENT = 0.2
WEIGHT_DISMISS_DECREMENT = -0.2
WEIGHT_ABANDON_DECREMENT = -0.04
WEIGHT_MIN = 0.0
WEIGHT_MAX = 5.0
DIFFICULTY_REWARD_MAP = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
}


def now_iso(dt=None):
    value = dt or timezone.now()
    return value.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")


def reward_points_by_difficulty(difficulty):
    try:
        difficulty = int(difficulty)
    except (TypeError, ValueError):
        difficulty = 3
    if difficulty < 1:
        difficulty = 1
    if difficulty > 5:
        difficulty = 5
    return DIFFICULTY_REWARD_MAP[difficulty]


def parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def error(status, message):
    return JsonResponse({"error": message}, status=status)


def parse_int_id(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    if "_" in raw:
        raw = raw.split("_", 1)[1]
    if not raw.isdigit():
        return None
    return int(raw)


def issue_token(user):
    AuthToken.objects.filter(user=user).delete()
    token = secrets.token_urlsafe(24)
    expires_at = timezone.now() + timedelta(seconds=3600)
    AuthToken.objects.create(user=user, token=token, expires_at=expires_at)
    return token, expires_at


def parse_deadline(value):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None:
        date_value = parse_date(value)
        if date_value:
            dt = datetime.combine(date_value, time.min)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone=dt_timezone.utc)
    return dt


def normalize_tags(value):
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = str(value).split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def set_user_tags(user, tag_type, tags):
    UserTag.objects.filter(user=user, tag__type=tag_type).delete()
    seen = set()
    for name in normalize_tags(tags):
        if name in seen:
            continue
        seen.add(name)
        tag, _ = Tag.objects.get_or_create(name=name, type=tag_type)
        UserTag.objects.create(user=user, tag=tag)
        # 手动编辑标签时将权重写为 1.0（覆盖）
        try:
            utw, created = UserTagWeight.objects.get_or_create(user=user, tag=tag)
            utw.weight = WEIGHT_MANUAL
            utw.save(update_fields=["weight", "updated_at"])
        except Exception:
            # 保守失败，不阻塞主流程
            pass
    # 用户标签更新后立即刷新 user 向量，减少推荐滞后
    try:
        SimilarityManager.generate_and_store_vector("user", str(user.id), force=True)
    except Exception:
        pass


def get_current_user(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    auth_token = AuthToken.objects.select_related("user").filter(token=token).first()
    if not auth_token:
        return None
    if auth_token.expires_at and auth_token.expires_at <= timezone.now():
        return None
    return auth_token.user


def require_auth(request):
    user = get_current_user(request)
    if not user:
        return None, error(401, "请先登录")
    return user, None


def user_response(user):
    return {
        "id": str(user.id),
        "nickname": user.nickname,
        "credit_score": user.credit_score,
        "points": user.points,
        "activity_points": user.activity_points,
        "has_honor": user.credit_score >= 85,
    }


def survey_response(survey):
    return {
        "id": str(survey.id),
        "title": survey.title,
        "description": survey.description,
        "link": None,
        "reward_points": survey.reward_points,
        "estimated_minutes": survey.estimated_minutes,
        "deadline": now_iso(survey.deadline) if survey.deadline else None,
        "status": survey.status,
        "created_at": now_iso(survey.created_at),
        "owner_id": str(survey.owner_id),
    }


def index(request):
    return HttpResponse(
        "Frontend is served by Vite. Start it from frontend/sixth_element.",
        content_type="text/plain; charset=utf-8",
    )


# ---- 验证码公共工具函数 -------------------------------------------------------

MAX_CODE_ATTEMPTS = 5  # 最多错误尝试次数
CODE_COOLDOWN_SECONDS = 60  # 同一邮笖68秒内不允许重发


def _hash_code(code: str) -> str:
    """SHA-256 摘要，存入数据库而不明文保存验证码。"""
    return hashlib.sha256(code.encode()).hexdigest()


def _send_verification_email(to_email: str, code: str, purpose: str):
    """调用 FallbackEmailBackend 发送验证码邮件（HTML 富文本）。"""
    if purpose == PasswordResetCode.PURPOSE_REGISTER:
        subject = "【第六元素】注册验证码"
        greeting = "您好，欢迎注册第六元素！"
        intro = "您正在注册第六元素账号，请使用以下验证码完成邮箱验证。"
        not_me = "如非本人操作，请忽略此邮件，您的账号安全不受任何影响。"
    else:
        subject = "【第六元素】密码重置验证码"
        greeting = "您好！"
        intro = "您正在重置第六元素账户密码，请使用以下验证码完成身份验证。"
        not_me = "如非本人操作，请忽略此邮件，您的账户密码不会发生任何改变。"

    # 纯文本备用（邮件客户端不支持 HTML 时显示）
    plain = (
        f"{subject}\n"
        f"{'─' * 30}\n\n"
        f"{greeting}\n\n"
        f"{intro}\n\n"
        f"验证码：{code}\n\n"
        f"（验证码 15 分钟内有效，请勿泄露给他人）\n\n"
        f"安全提示：请勿将验证码告知任何人，平台工作人员不会向您索要验证码。\n\n"
        f"{'─' * 30}\n"
        f"{not_me}\n\n"
        f"此邮件由系统自动发送，请勿直接回复。\n"
        f"第六元素团队"
    )

    # HTML 富文本（table 布局保障兼容性；避免装饰性文字以便剥标签后仍可读）
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{subject}</title></head>
<body style="margin:0;padding:0;background:#eef2fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#eef2fb;padding:40px 16px;">
  <tr><td align="center">
    <table width="540" cellpadding="0" cellspacing="0" border="0" style="max-width:540px;width:100%;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,82,217,0.10);">

      <!-- 顶部渐变 Banner -->
      <tr>
        <td style="background:linear-gradient(135deg,#0052d9 0%,#3d7fff 100%);padding:32px 44px;text-align:center;">
          <div style="color:#ffffff;font-size:24px;font-weight:700;letter-spacing:1px;">第六元素</div>
          <div style="color:rgba(255,255,255,0.55);font-size:11px;margin-top:6px;">校园问卷互助平台</div>
        </td>
      </tr>

      <!-- 正文区域 -->
      <tr>
        <td style="padding:40px 44px 32px;">
          <p style="font-size:17px;font-weight:600;color:#0b2b66;margin:0 0 10px 0;">{greeting}</p>
          <p style="font-size:14px;color:#4c5e78;line-height:1.85;margin:0 0 28px 0;">{intro}</p>

          <!-- 验证码卡片 -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0"
            style="background:#f0f6ff;border:2px solid #90b4f7;border-radius:12px;margin-bottom:20px;">
            <tr>
              <td style="padding:28px 20px;text-align:center;">
                <div style="font-size:42px;font-weight:800;letter-spacing:12px;color:#0052d9;font-family:'Courier New',Courier,monospace;padding-left:12px;">{code}</div>
                <p style="font-size:12px;color:#7b96b8;margin:12px 0 0 0;">验证码 15 分钟内有效，请勿泄露给他人</p>
              </td>
            </tr>
          </table>

          <!-- 安全提示 -->
          <p style="font-size:13px;color:#7a5c2a;background:#fffbf0;border-left:4px solid #f5a623;padding:12px 16px;border-radius:0 8px 8px 0;margin:0 0 20px 0;line-height:1.75;">
            <strong>安全提示：</strong>请勿将验证码告知任何人，平台工作人员不会向您索要验证码。
          </p>

          <p style="font-size:13px;color:#bac8d8;line-height:1.75;margin:0;">{not_me}</p>
        </td>
      </tr>

      <!-- 分隔线 -->
      <tr>
        <td style="padding:0 44px;"><hr style="border:none;border-top:1px solid #e8eef8;margin:0;"></td>
      </tr>

      <!-- 页脚 -->
      <tr>
        <td style="background:#f8faff;padding:18px 44px;text-align:center;">
          <p style="font-size:12px;color:#bac8d8;margin:0 0 4px 0;">此邮件由系统自动发送，请勿直接回复</p>
          <p style="font-size:12px;color:#d0dae8;margin:0;">&copy; 2025 第六元素团队</p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body></html>"""

    send_mail(
        subject=subject,
        message=plain,
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        html_message=html,
        fail_silently=False,
    )


def _issue_code(email: str, purpose: str) -> str | None:
    """
    为指定邮符1和 purpose 创建新验证码记录。
    如果处于冷却期内，返回 None （调用方应返回 429）。
    """
    last = (
        PasswordResetCode.objects.filter(email=email, purpose=purpose)
        .order_by("-created_at")
        .first()
    )
    if last is not None:
        elapsed = (timezone.now() - last.created_at).total_seconds()
        if elapsed < CODE_COOLDOWN_SECONDS:
            return None  # 还在冷却期

    # 使旧验证码全部失效
    PasswordResetCode.objects.filter(
        email=email, purpose=purpose, is_used=False
    ).update(is_used=True)

    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    PasswordResetCode.objects.create(
        email=email,
        code_hash=_hash_code(code),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=15),
        is_used=False,
        attempt_count=0,
    )
    return code


def _verify_code(email: str, code: str, purpose: str):
    """
    验证码验证。
    返回 (PasswordResetCode 对象, None) 或 (None, error_response)。
    """
    record = (
        PasswordResetCode.objects.filter(
            email=email,
            purpose=purpose,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )
    if not record:
        return None, error(401, "验证码无效或已过期")

    if record.attempt_count >= MAX_CODE_ATTEMPTS:
        record.is_used = True
        record.save(update_fields=["is_used"])
        return None, error(401, "验证码错误次数过多，请重新获取验证码")

    if record.code_hash != _hash_code(code):
        record.attempt_count += 1
        record.save(update_fields=["attempt_count"])
        remaining = MAX_CODE_ATTEMPTS - record.attempt_count
        return None, error(401, f"验证码错误，还剩 {remaining} 次机会")

    return record, None


# ---- 验证 & 注册路由 -----------------------------------------------------------


@csrf_exempt
def send_register_code(request):
    """注册前发送邮符1验证码（防止击包占号）。"""
    if request.method != "POST":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    email = data.get("email", "").strip()
    if not email:
        return error(422, "邮箱地址不能为空")
    if AppUser.objects.filter(email=email).exists():
        return error(422, "该邮箱已被注册")

    code = _issue_code(email, PasswordResetCode.PURPOSE_REGISTER)
    if code is None:
        return error(429, "发送频率过高，请稍后再试")

    try:
        _send_verification_email(email, code, PasswordResetCode.PURPOSE_REGISTER)
    except Exception:
        return error(500, "邮件发送失败，请稍后重试")

    return JsonResponse({"message": "verification code sent", "expires_in": 900})


@csrf_exempt
def register(request):
    """两步注册：先经过 send_register_code 获取验证码，再提交此接口完成注册。"""
    if request.method != "POST":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()
    code = data.get("code", "").strip()
    if not email or not password or not nickname or not code:
        return error(422, "邮箱、密码、昵称和验证码均不能为空")
    if len(password) < 6:
        return error(422, "密码长度至少为6位")
    if AppUser.objects.filter(email=email).exists():
        return error(422, "该邮箱已被注册")

    record, err = _verify_code(email, code, PasswordResetCode.PURPOSE_REGISTER)
    if err:
        return err

    user = AppUser.objects.create(
        email=email,
        nickname=nickname,
        credit_score=80,
        points=20,
        activity_points=0,
        status="normal",
    )
    AuthCredential.objects.create(user=user, password_hash=make_password(password))
    record.is_used = True
    record.save(update_fields=["is_used"])
    token, _ = issue_token(user)
    return JsonResponse(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": str(user.id), "nickname": user.nickname},
        }
    )


@csrf_exempt
def login(request):
    if request.method != "POST":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if not email or not password:
        return error(422, "邮箱和密码不能为空")

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return error(401, "邮箱或密码错误")

    credential = AuthCredential.objects.filter(user=user).first()
    if not credential or not check_password(password, credential.password_hash):
        return error(401, "邮箱或密码错误")

    token, _ = issue_token(user)
    return JsonResponse(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": str(user.id), "nickname": user.nickname},
        }
    )


@csrf_exempt
<<<<<<< Updated upstream
def send_reset_code(request):
    """发送密码重置验证码。"""
    if request.method != "POST":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    email = data.get("email", "").strip()
    if not email:
        return error(422, "邮箱地址不能为空")
    if not AppUser.objects.filter(email=email).exists():
        return error(404, "用户不存在")

    code = _issue_code(email, PasswordResetCode.PURPOSE_RESET)
    if code is None:
        return error(429, "发送频率过高，请稍后再试")

    try:
        _send_verification_email(email, code, PasswordResetCode.PURPOSE_RESET)
    except Exception:
        return error(500, "邮件发送失败，请稍后重试")

    return JsonResponse({"message": "verification code sent", "expires_in": 900})
=======
def request_password_reset(request):
    """请求密码重置，发送验证码"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    
    data = parse_json(request)
    email = data.get("email", "").strip()
    
    if not email:
        return error(422, "email required")
    
    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        # 为了安全，不暴露邮箱是否存在
        return JsonResponse({"message": "如果邮箱存在，验证码已发送"})
    
    # 生成6位数字验证码
    reset_code = ''.join(random.choices(string.digits, k=6))
    
    # 删除之前未使用的重置令牌
    PasswordReset.objects.filter(user=user, is_used=False).delete()
    
    # 创建新的重置令牌，有效期15分钟
    expires_at = timezone.now() + timedelta(minutes=15)
    PasswordReset.objects.create(
        user=user,
        reset_code=reset_code,
        expires_at=expires_at
    )
    
    # TODO: 在生产环境中通过邮件发送验证码
    # 这里可以集成邮件服务（如 SendGrid、AWS SES 等）
    print(f"[DEBUG] Password reset code for {email}: {reset_code}")
    
    return JsonResponse({"message": "验证码已发送"})
>>>>>>> Stashed changes


@csrf_exempt
def verify_reset_code(request):
<<<<<<< Updated upstream
    """验证重置码并重置密码。"""
    if request.method != "POST":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    email = data.get("email", "").strip()
    code = data.get("code", "").strip()
    new_password = data.get("new_password", "").strip()
    if not email or not code or not new_password:
        return error(422, "邮箱、验证码和新密码不能为空")
    if len(new_password) < 6:
        return error(422, "密码长度至少为6位")

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return error(404, "用户不存在")

    record, err = _verify_code(email, code, PasswordResetCode.PURPOSE_RESET)
    if err:
        return err

    credential = AuthCredential.objects.filter(user=user).first()
    if credential:
        credential.password_hash = make_password(new_password)
        credential.save()
    else:
        AuthCredential.objects.create(
            user=user, password_hash=make_password(new_password)
        )

    record.is_used = True
    record.save(update_fields=["is_used"])
    AuthToken.objects.filter(user=user).delete()

    return JsonResponse(
        {
            "message": "password reset successful",
            "user": {"id": str(user.id), "nickname": user.nickname},
        }
    )
=======
    """验证密码重置码"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    
    data = parse_json(request)
    email = data.get("email", "").strip()
    reset_code = data.get("reset_code", "").strip()
    
    if not email or not reset_code:
        return error(422, "email and reset_code required")
    
    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return error(401, "invalid email")
    
    # 查找有效的重置令牌
    reset_record = PasswordReset.objects.filter(
        user=user,
        reset_code=reset_code,
        is_used=False,
        expires_at__gt=timezone.now()
    ).first()
    
    if not reset_record:
        return error(401, "invalid or expired reset code")
    
    return JsonResponse({"message": "验证码正确"})


@csrf_exempt
def reset_password(request):
    """重置密码"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    
    data = parse_json(request)
    email = data.get("email", "").strip()
    reset_code = data.get("reset_code", "").strip()
    new_password = data.get("new_password", "").strip()
    
    if not email or not reset_code or not new_password:
        return error(422, "email, reset_code, and new_password required")
    
    if len(new_password) < 6:
        return error(422, "password must be at least 6 characters")
    
    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return error(401, "invalid email")
    
    # 验证重置令牌
    reset_record = PasswordReset.objects.filter(
        user=user,
        reset_code=reset_code,
        is_used=False,
        expires_at__gt=timezone.now()
    ).first()
    
    if not reset_record:
        return error(401, "invalid or expired reset code")
    
    # 更新密码
    credential = AuthCredential.objects.filter(user=user).first()
    if credential:
        credential.password_hash = make_password(new_password)
        credential.save(update_fields=["password_hash"])
    else:
        # 如果没有凭证记录，创建一个
        AuthCredential.objects.create(
            user=user,
            password_hash=make_password(new_password)
        )
    
    # 标记重置码为已使用
    reset_record.is_used = True
    reset_record.used_at = timezone.now()
    reset_record.save(update_fields=["is_used", "used_at"])
    
    # 删除该用户的所有认证令牌（强制重新登录）
    AuthToken.objects.filter(user=user).delete()
    
    return JsonResponse({"message": "密码已成功重置，请用新密码登录"})

>>>>>>> Stashed changes


@csrf_exempt
def user_me(request):
    user, err = require_auth(request)
    if err:
        return err
    if request.method == "GET":
        return JsonResponse(user_response(user))
    if request.method != "PATCH":
        return error(405, "请求方法不允许")
    data = parse_json(request)
    nickname = data.get("nickname", user.nickname)
    school = data.get("school", None)
    tags = data.get("tags", None)
    user.nickname = nickname
    user.save(update_fields=["nickname"])
    if school is not None:
        set_user_tags(user, "school", [school] if school else [])
    if tags is not None:
        set_user_tags(user, "interest", tags)
    return JsonResponse(user_response(user))


@csrf_exempt
def surveys(request):
    if request.method == "POST":
        user, err = require_auth(request)
        if err:
            return err
        data = parse_json(request)
        title = data.get("title", "").strip()
        reward_points = int(data.get("reward_points", 0) or 0)
        if not title:
            return error(422, "问卷标题不能为空")
        if reward_points < 0:
            return error(422, "悬赏积分不能为负数")
        if user.points < reward_points:
            return error(422, "积分不足，无法发布问卷")

        survey = Survey.objects.create(
            owner=user,
            title=title,
            description=data.get("description"),
            reward_points=reward_points,
            publish_cost_points=reward_points,
            deadline=parse_deadline(data.get("deadline")),
            estimated_minutes=data.get("estimated_minutes"),
            status="published",
        )
        questionnaire = Questionnaire.objects.create(
            survey=survey,
            version=1,
            status="published",
            title=title,
        )
        survey.active_questionnaire = questionnaire
        survey.save(update_fields=["active_questionnaire"])
        if reward_points > 0:
            user.points -= reward_points
            user.save(update_fields=["points"])
            PointsLog.objects.create(
                user=user,
                points_type="publish_cost",
                delta=-reward_points,
                reason="发布问卷消耗",
            )
        # generate survey vector at creation time (best-effort)
        try:
            from core.services.similarity_service import SimilarityService

            SimilarityService.generate_and_store_vector("survey", str(survey.id))
        except Exception:
            pass
        return JsonResponse({"id": str(survey.id), "status": "active"})

    if request.method != "GET":
        return error(405, "请求方法不允许")

    status = request.GET.get("status")
    min_points = request.GET.get("min_points")
    max_minutes = request.GET.get("max_minutes")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    queryset = Survey.objects.all().order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    if min_points:
        queryset = queryset.filter(reward_points__gte=int(min_points))
    if max_minutes:
        queryset = queryset.filter(estimated_minutes__lte=int(max_minutes))

    total = queryset.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": str(survey.id),
            "title": survey.title,
            "reward_points": survey.reward_points,
            "estimated_minutes": survey.estimated_minutes,
            "deadline": now_iso(survey.deadline) if survey.deadline else None,
        }
        for survey in queryset[offset : offset + page_size]
    ]
    return JsonResponse(
        {"items": items, "page": page, "page_size": page_size, "total": total}
    )


def survey_detail(request, survey_id):
    if request.method != "GET":
        return error(405, "请求方法不允许")
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "无效的问卷ID")
    try:
        survey = Survey.objects.get(id=survey_pk)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")
    return JsonResponse(survey_response(survey))


@csrf_exempt
def close_survey(request, survey_id):
    if request.method != "POST":
        return error(405, "请求方法不允许")
    user, err = require_auth(request)
    if err:
        return err
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "无效的问卷ID")
    try:
        survey = Survey.objects.get(id=survey_pk)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")
    if survey.owner_id != user.id:
        return error(403, "您不是该问卷的所有者")
    survey.status = "closed"
    survey.save(update_fields=["status"])
    return JsonResponse({"id": str(survey.id), "status": "closed"})


@csrf_exempt
def submit_fill(request, survey_id):
    if request.method != "POST":
        return error(405, "请求方法不允许")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    duration = data.get("duration_seconds")
    survey_pk = parse_int_id(survey_id)
    if survey_pk is None:
        return error(422, "无效的问卷ID")
    try:
        survey = Survey.objects.get(id=survey_pk)
    except Survey.DoesNotExist:
        return error(404, "问卷不存在")
    if survey.status != "published":
        return error(422, "问卷未发布")
    if survey.owner_id == user.id:
        return error(422, "不能填写自己发布的问卷")
    if Response.objects.filter(survey=survey, user=user).exists():
        return error(422, "您已经填写过该问卷")

    response = Response.objects.create(
        survey=survey,
        questionnaire=survey.active_questionnaire,
        user=user,
        duration_seconds=duration,
        status="submitted",
        submitted_at=timezone.now(),
    )
    # 提交问卷时增加用户与问卷主要 tag 的权重（初始记录为 0，按 WEIGHT_INCREMENT 增加）
    try:
        survey_tags = survey.surveytag_set.select_related("tag").all()
        for st in survey_tags:
            tag = st.tag
            utw, created = UserTagWeight.objects.get_or_create(user=user, tag=tag)
            new_w = utw.weight + WEIGHT_INCREMENT
            if new_w > WEIGHT_MAX:
                new_w = WEIGHT_MAX
            utw.weight = new_w
            utw.save(update_fields=["weight", "updated_at"])
    except Exception:
        # 权重更新失败不影响主要提交流程
        pass
    # 提交后使用户向量失效，下次推荐时重新生成
    try:
        SimilarityManager.invalidate_vector("user", str(user.id))
    except Exception:
        pass
    return JsonResponse(
        {"id": str(response.id), "status": response.status, "points_awarded": 0}
    )


@csrf_exempt
def review_fill(request, fill_id):
    if request.method != "POST":
        return error(405, "请求方法不允许")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    status = data.get("status")
    if status not in ("approved", "rejected"):
        return error(422, "审核状态必须为 approved 或 rejected")
    response_pk = parse_int_id(fill_id)
    if response_pk is None:
        return error(422, "无效的填写记录ID")

    try:
        record = Response.objects.select_related("survey", "user").get(id=response_pk)
    except Response.DoesNotExist:
        return error(404, "填写记录不存在")
    if record.survey.owner_id != user.id:
        return error(403, "您不是该问卷的所有者")
    if record.status != "submitted":
        return error(422, "该填写记录已审核")

    points_awarded = 0
    if status == "approved":
        already_rewarded = PointsLog.objects.filter(
            user=record.user,
            points_type="fill_reward",
            ref_type="survey",
            ref_id=record.survey_id,
        ).exists()
        if not already_rewarded:
            points_awarded = reward_points_by_difficulty(record.survey.difficulty)
            record.user.points += points_awarded
            record.user.activity_points += points_awarded
            record.user.save(update_fields=["points", "activity_points"])
            PointsLog.objects.create(
                user=record.user,
                points_type="fill_reward",
                delta=points_awarded,
                reason="完成问卷审核通过",
                ref_type="survey",
                ref_id=record.survey_id,
            )

    record.status = status
    record.save(update_fields=["status"])
    return JsonResponse(
        {"id": str(record.id), "status": status, "points_awarded": points_awarded}
    )


def my_fills(request):
    if request.method != "GET":
        return error(405, "请求方法不允许")
    user, err = require_auth(request)
    if err:
        return err
    status = request.GET.get("status")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    queryset = Response.objects.filter(user=user).order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    total = queryset.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": str(record.id),
            "survey_id": str(record.survey_id),
            "status": record.status,
            "created_at": now_iso(record.created_at),
        }
        for record in queryset[offset : offset + page_size]
    ]
    return JsonResponse(
        {"items": items, "page": page, "page_size": page_size, "total": total}
    )


def points_logs(request):
    if request.method != "GET":
        return error(405, "请求方法不允许")
    user, err = require_auth(request)
    if err:
        return err
    log_type = request.GET.get("type")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    queryset = PointsLog.objects.filter(user=user).order_by("-created_at")
    if log_type == "earn":
        queryset = queryset.filter(points_type__in=["reward", "admin_adjust"])
    elif log_type == "spend":
        queryset = queryset.filter(points_type__in=["publish_cost", "admin_adjust"])

    total = queryset.count()
    offset = (page - 1) * page_size
    items = []

    for log in queryset[offset : offset + page_size]:
        # Try to find associated survey or fill record for navigation
        related_id = None
        related_type = None

        if "问卷" in log.reason or "填" in log.reason:
            # Try to find matching fill record by timestamp and delta
            try:
                if log.delta > 0:  # Earn - likely from completing a survey
                    fill = Response.objects.filter(
                        user=user, created_at__date=log.created_at.date()
                    ).first()
                    if fill:
                        related_id = str(fill.survey_id)
                        related_type = "survey_fill"
                elif log.delta < 0:  # Spend - likely from publishing
                    survey = Survey.objects.filter(
                        owner=user,
                        reward_points=-log.delta,
                        created_at__date=log.created_at.date(),
                    ).first()
                    if survey:
                        related_id = str(survey.id)
                        related_type = "survey_publish"
            except:
                pass

        items.append(
            {
                "id": str(log.id),
                "delta": log.delta,
                "reason": log.reason,
                "created_at": now_iso(log.created_at),
                "related_id": related_id,
                "related_type": related_type,
            }
        )

    # Calculate honor status: credit_score >= 85 = qualified
    has_honor = user.credit_score >= 85

    return JsonResponse(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "user": {
                "id": str(user.id),
                "points": user.points,
                "credit_score": user.credit_score,
                "activity_points": user.activity_points,
                "has_honor": has_honor,
            },
        }
    )


@csrf_exempt
def create_report(request):
    if request.method != "POST":
        return error(405, "请求方法不允许")
    user, err = require_auth(request)
    if err:
        return err
    data = parse_json(request)
    target_type = data.get("target_type", "").strip()
    target_id_raw = data.get("target_id", "")
    reason = data.get("reason", "").strip()
    if not target_type or not target_id_raw or not reason:
        return error(422, "举报目标类型、目标ID和原因不能为空")

    target_id = parse_int_id(target_id_raw)
    if target_id is None:
        return error(422, "无效的目标ID")
    if target_type == "survey":
        if not Survey.objects.filter(id=target_id).exists():
            return error(404, "问卷不存在")
    elif target_type == "user":
        if not AppUser.objects.filter(id=target_id).exists():
            return error(404, "用户不存在")
    else:
        return error(422, "举报目标类型必须为 survey 或 user")

    report = Report.objects.create(
        reporter=user,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        status="open",
    )
    return JsonResponse({"id": str(report.id), "status": report.status})
