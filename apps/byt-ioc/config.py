import os
from pathlib import Path

from sqlmesh.core.config import (
    Config,
    GatewayConfig,
    ModelDefaultsConfig,
    PostgresConnectionConfig,
)


def _load_dotenv_if_present() -> None:
    """Load key/value pairs from .env into process env if not already set."""
    env_path = Path(__file__).resolve().parent / ".env"
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


_load_dotenv_if_present()

# ---------------------------------------------------------------------------
# BI database: destination where all transformed models are materialised.
# ---------------------------------------------------------------------------
_ioc = PostgresConnectionConfig(
    host=os.environ.get("IOC_DB_HOST", "localhost"),
    port=int(os.environ.get("IOC_DB_PORT", "5432")),
    database=os.environ.get("IOC_DB_NAME", "bi"),
    user=os.environ.get("IOC_DB_USER", "user"),
    password=os.environ.get("IOC_DB_PASSWORD", ""),
)

# SQLMesh state is stored in a dedicated database by default. If state DB env
# vars are missing, it falls back to BI DB for backward compatibility.
_state = PostgresConnectionConfig(
    host=os.environ.get("SQLMESH_STATE_DB_HOST", os.environ.get("IOC_DB_HOST", "localhost")),
    port=int(os.environ.get("SQLMESH_STATE_DB_PORT", os.environ.get("IOC_DB_PORT", "5432"))),
    database=os.environ.get("SQLMESH_STATE_DB_NAME", os.environ.get("IOC_DB_NAME", "bi")),
    user=os.environ.get("SQLMESH_STATE_DB_USER", os.environ.get("IOC_DB_USER", "user")),
    password=os.environ.get("SQLMESH_STATE_DB_PASSWORD", os.environ.get("IOC_DB_PASSWORD", "")),
)

config = Config(
    gateways={
        "ioc": GatewayConfig(
            connection=_ioc,
            state_connection=_state,
            state_schema="sqlmesh_state",
        ),
    },
    default_gateway="ioc",
    physical_schema_mapping={"^sqlmesh_work$": "sw"},

    model_defaults=ModelDefaultsConfig(dialect="postgres"),
)
