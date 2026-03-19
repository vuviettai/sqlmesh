"""Load .env file into process environment variables."""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv_if_present() -> None:
    """Walk up two directories from this file to find the project-level .env."""
    env_path = Path(__file__).resolve().parents[4] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)
