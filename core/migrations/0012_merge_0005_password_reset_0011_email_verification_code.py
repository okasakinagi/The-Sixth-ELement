# Merge migration to resolve divergent 0005 branches.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_password_reset"),
        ("core", "0011_email_verification_code"),
    ]

    operations = []
