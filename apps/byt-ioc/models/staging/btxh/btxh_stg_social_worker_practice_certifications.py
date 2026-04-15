"""Explode SocialWorkers.practiceCertifications into sqlmesh_work.btxh_stg_sw_prac_cert."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import explode_social_worker_practice_certifications
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "social_worker_id": "text",
    "updated_at": "timestamp",
    "practice_certification_id": "text",
    "certificate_number": "text",
    "certificate_name": "text",
    "issued_by": "text",
    "issued_date": "date",
    "expiry_date": "date",
    "status": "text",
}

TIMESTAMP_COLUMNS = ("_airbyte_extracted_at", "updated_at")
DATE_COLUMNS = ("issued_date", "expiry_date")
INTEGER_COLUMNS = ("_airbyte_generation_id",)
FETCH_BATCH_SIZE = 5_000


def _normalize_dataframe(records: list[dict[str, t.Any]]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records)
    df = df.reindex(columns=MODEL_COLUMNS.keys())

    for col in TIMESTAMP_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    for col in INTEGER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    return df.astype(object).where(pd.notna(df), None)


@model(
    "sqlmesh_work.btxh_stg_sw_prac_cert",
    description=(
        "Exploded BTXH social worker practice certifications from public.\"SocialWorkers\" "
        "with one row per certification."
    ),
    physical_schema_override="sw",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="updated_at", batch_size=90),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["practice_certification_id"],
    columns=MODEL_COLUMNS,
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> t.Iterator[pd.DataFrame]:
    del context, execution_time, kwargs

    load_dotenv_if_present()
    conn = get_connection()
    try:
        schema_name = os.environ.get("STAGING_DB_SCHEMA", "public")
        table_name = os.environ.get("STAGING_BTXH_SOCIAL_WORKER_SOURCE_TABLE", "SocialWorkers")
        query = sql.SQL(
            """
            SELECT
                _airbyte_raw_id,
                _airbyte_extracted_at,
                _airbyte_generation_id,
                id,
                "updatedAt",
                "updatedAtmm",
                "practiceCertifications"
            FROM {schema}.{table}
            WHERE COALESCE(
                TO_TIMESTAMP("updatedAt" / 1000.0),
                TO_TIMESTAMP(NULLIF("updatedAtmm", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
            ) >= %(start)s
              AND COALESCE(
                TO_TIMESTAMP("updatedAt" / 1000.0),
                TO_TIMESTAMP(NULLIF("updatedAtmm", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
              ) < %(end)s
            """
        ).format(schema=sql.Identifier(schema_name), table=sql.Identifier(table_name))

        with conn.cursor() as cur:
            cur.execute(query, {"start": start, "end": end})
            while True:
                rows = cur.fetchmany(FETCH_BATCH_SIZE)
                if not rows:
                    break

                records: list[dict[str, t.Any]] = []
                for row in rows:
                    records.extend(explode_social_worker_practice_certifications(dict(row)))

                if records:
                    yield _normalize_dataframe(records)
    finally:
        conn.close()