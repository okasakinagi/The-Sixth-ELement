from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Survey
from core.points import reward_points_for_difficulty


class Command(BaseCommand):
    help = "Sync Survey.reward_points from Survey.difficulty."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        surveys = list(Survey.objects.all().only("id", "title", "difficulty", "reward_points"))

        changed = []
        for survey in surveys:
            expected_reward = reward_points_for_difficulty(survey.difficulty)
            current_reward = survey.reward_points or 0
            if current_reward == expected_reward:
                continue
            changed.append(
                {
                    "survey": survey,
                    "current_reward": current_reward,
                    "expected_reward": expected_reward,
                }
            )

        if not changed:
            self.stdout.write(self.style.SUCCESS("All survey reward points are already in sync."))
            return

        self.stdout.write(
            f"Found {len(changed)} survey(s) with inconsistent reward_points."
        )
        for item in changed[:20]:
            survey = item["survey"]
            self.stdout.write(
                f"  - survey #{survey.id} {survey.title}: {item['current_reward']} -> {item['expected_reward']}"
            )
        if len(changed) > 20:
            self.stdout.write(f"  ... and {len(changed) - 20} more")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run only. No data was changed."))
            transaction.set_rollback(True)
            return

        for item in changed:
            survey = item["survey"]
            survey.reward_points = item["expected_reward"]

        Survey.objects.bulk_update([item["survey"] for item in changed], ["reward_points"])
        self.stdout.write(self.style.SUCCESS(f"Updated {len(changed)} survey(s)."))