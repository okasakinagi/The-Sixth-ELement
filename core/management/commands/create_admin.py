import hashlib

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import AppUser, AuthCredential, Role, UserRole


class Command(BaseCommand):
    help = "Create an admin user."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="")
        parser.add_argument("--password", type=str, default="")
        parser.add_argument("--nickname", type=str, default="系统管理员")

    @transaction.atomic
    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        nickname = options["nickname"]

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

        password_hash = hashlib.sha256(password.encode()).hexdigest()
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

        self.stdout.write(self.style.SUCCESS(f"\nAdmin user created successfully!"))
        self.stdout.write(f"  Email: {email}")
        self.stdout.write(f"  Password: {password}")
