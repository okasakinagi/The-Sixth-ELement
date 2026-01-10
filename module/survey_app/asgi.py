import os

import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

project_root = Path(__file__).resolve().parent.parent.parent
module_dir = project_root / "module"
for path in (str(module_dir), str(project_root)):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "survey_app.settings")

application = get_asgi_application()
