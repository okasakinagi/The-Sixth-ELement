#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    module_dir = project_root / "module"
    if module_dir.exists():
        sys.path.insert(0, str(module_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "survey_app.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
