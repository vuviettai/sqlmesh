"""psycopg2 connection factory for the staging database."""
from __future__ import annotations

import os

import psycopg2
import psycopg2.extras


def get_connection() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection to the staging PostgreSQL database.

    Required env vars: STAGING_DB_HOST, STAGING_DB_NAME, STAGING_DB_USER,
                       STAGING_DB_PASSWORD
    Optional env vars: STAGING_DB_PORT (default 5432)
    """
    return psycopg2.connect(
        host=os.environ["STAGING_DB_HOST"],
        port=int(os.environ.get("STAGING_DB_PORT", "5432")),
        dbname=os.environ["STAGING_DB_NAME"],
        user=os.environ["STAGING_DB_USER"],
        password=os.environ["STAGING_DB_PASSWORD"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
