"""
双账户 Fallback SMTP Email Backend
优先使用主账户发送，主账户遇到 SMTP 异常时自动切换备用账户，对用户完全无感。
两个账户使用相同的显示名，邮件头 From 格式：第六元素 <account@domain.com>
"""

import logging
import os

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

logger = logging.getLogger(__name__)


def _build_accounts():
    """从环境变量读取两个发件账户配置。"""
    display_name = os.environ.get("EMAIL_DISPLAY_NAME", "第六元素")
    accounts = []

    primary_user = os.environ.get("EMAIL_PRIMARY_USER", "")
    primary_pass = os.environ.get("EMAIL_PRIMARY_PASSWORD", "")
    if primary_user and primary_pass:
        accounts.append(
            {
                "host": os.environ.get("EMAIL_HOST", "smtp.exmail.qq.com"),
                "port": int(os.environ.get("EMAIL_PORT", "465")),
                "username": primary_user,
                "password": primary_pass,
                "use_ssl": os.environ.get("EMAIL_USE_SSL", "true").lower() == "true",
                "use_tls": os.environ.get("EMAIL_USE_TLS", "false").lower() == "true",
                "from_email": f"{display_name} <{primary_user}>",
            }
        )

    fallback_user = os.environ.get("EMAIL_FALLBACK_USER", "")
    fallback_pass = os.environ.get("EMAIL_FALLBACK_PASSWORD", "")
    if fallback_user and fallback_pass:
        accounts.append(
            {
                "host": os.environ.get("EMAIL_HOST", "smtp.exmail.qq.com"),
                "port": int(os.environ.get("EMAIL_PORT", "465")),
                "username": fallback_user,
                "password": fallback_pass,
                "use_ssl": os.environ.get("EMAIL_USE_SSL", "true").lower() == "true",
                "use_tls": os.environ.get("EMAIL_USE_TLS", "false").lower() == "true",
                "from_email": f"{display_name} <{fallback_user}>",
            }
        )

    return accounts


class FallbackEmailBackend:
    """
    多账户降级邮件 backend。
    依次尝试每个账户，第一个成功即返回，全部失败才抛出异常。
    """

    def __init__(self, **kwargs):
        self.accounts = _build_accounts()
        if not self.accounts:
            raise RuntimeError(
                "未配置任何邮件账户，请检查环境变量 EMAIL_PRIMARY_USER / EMAIL_PRIMARY_PASSWORD"
            )

    def open(self):
        pass

    def close(self):
        pass

    def send_messages(self, email_messages):
        """
        遍历账户列表，使用第一个可用账户发送所有邮件。
        发送前将每封邮件的 from_email 替换为当前账户地址。
        """
        last_exc = None
        for account in self.accounts:
            try:
                backend = SMTPEmailBackend(
                    host=account["host"],
                    port=account["port"],
                    username=account["username"],
                    password=account["password"],
                    use_ssl=account["use_ssl"],
                    use_tls=account["use_tls"],
                    fail_silently=False,
                )
                # 替换发件人为当前账户（显示名保持一致）
                for msg in email_messages:
                    msg.from_email = account["from_email"]

                sent = backend.send_messages(email_messages)
                if account["username"] != self.accounts[0]["username"]:
                    logger.warning(
                        "主邮件账户不可用，已通过备用账户 %s 发送邮件",
                        account["username"],
                    )
                return sent
            except Exception as exc:
                logger.error(
                    "邮件账户 %s 发送失败: %s，尝试下一个账户",
                    account["username"],
                    exc,
                )
                last_exc = exc
                continue

        raise RuntimeError(f"所有邮件账户均发送失败，最后一个错误：{last_exc}") from last_exc
