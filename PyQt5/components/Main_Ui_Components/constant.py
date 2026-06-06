import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Re-export for backward compatibility
__all__ = [
    "BASE_DIR",
    "BACKEND_BASE_URL",
    "APP_VERSION",
    "get_logo_display_size",
    "get_large_logo_display_size",
    "DATE_DISPLAY_FORMAT",
]


def load_dotenv():
    if getattr(sys, "frozen", False):
        # If running as an EXE, look for .env in the same folder as the EXE
        env_path = Path(sys.executable).parent / ".env"
    else:
        # If running as script, look in the project root
        env_path = BASE_DIR / ".env"

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip()
                    # Support inline comments in .env values, e.g. URL=... # prod
                    if " #" in value:
                        value = value.split(" #", 1)[0].strip()
                    value = value.strip().strip("'").strip('"')
                    os.environ.setdefault(key.strip(), value)


load_dotenv()

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")
APP_VERSION = os.getenv("APP_VERSION", "V1.0.0")

LOGO_DISPLAY_SIZE = 200
LARGE_LOGO_DISPLAY_SIZE = 200


def get_logo_display_size() -> int:
    from .ui_scale import scale_int

    return scale_int(LOGO_DISPLAY_SIZE)


def get_large_logo_display_size() -> int:
    from .ui_scale import scale_int

    return scale_int(LARGE_LOGO_DISPLAY_SIZE)


DATE_DISPLAY_FORMAT = "yyyy-MM-dd"
