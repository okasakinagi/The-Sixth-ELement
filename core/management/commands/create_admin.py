import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import AppUser, AuthCredential, Role, UserRole


class Command(BaseCommand):
    help = "Create an admin user."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="")
        parser.add_argument("--nickname", type=str, default="系统管理员")

    def handle(self, *args, **options):
        email = options["email"]
        nickname = options["nickname"]

        if not email:
            email = input("请输入管理员邮箱: ").strip()

        password = getpass.getpass("请输入密码: ")
        if not password:
            password = getpass.getpass("密码不能为空，请重新输入: ")

        # 增强密码强度检查
        import re
        errors = []
        if len(password) < 8:
            errors.append("密码长度至少8位")
        if not re.search(r'[A-Z]', password):
            errors.append("密码至少包含一个大写字母")
        if not re.search(r'[a-z]', password):
            errors.append("密码至少包含一个小写字母")
        if not re.search(r'[0-9]', password):
            errors.append("密码至少包含一个数字")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码至少包含一个特殊字符")

        if errors:
            for error in errors:
                self.stdout.write(self.style.ERROR(f"- {error}"))
            return

        admin_role, _ = Role.objects.get_or_create(
            name="admin", defaults={"description": "系统管理员"}
        )

        user, created = AppUser.objects.get_or_create(
            email=email,
            defaults={
                "nickname": nickname,
                "credit_score": 100,
                "points": 0,
                "activity_points": 0,
            },
        )

        if created:
            self.stdout.write(f"Created user: {email}")
        else:
            self.stdout.write(f"User already exists: {email}")

        password_hash = make_password(password)
        cred, cred_created = AuthCredential.objects.get_or_create(
            user=user,
            defaults={"password_hash": password_hash},
        )

        if cred_created:
            self.stdout.write(f"Created credential for: {email}")
        else:
            cred.password_hash = password_hash
            cred.save(update_fields=["password_hash"])
            self.stdout.write(f"Updated password for: {email}")

        UserRole.objects.get_or_create(user=user, role=admin_role)
        self.stdout.write(f"Assigned admin role to: {email}")

        # 记录审计日志
        from core.models import AuditLog
        AuditLog.objects.create(
            target_type="AppUser",
            target_id=user.id,
            action="create_admin",
            operator=None,  # 系统操作
            note=f"创建/更新管理员账户: {email}"
        )

        self.stdout.write(self.style.SUCCESS(f"\nAdmin user created successfully!"))
        self.stdout.write(f"  Email: {email}")
        self.stdout.write(f"  Password: ****")
