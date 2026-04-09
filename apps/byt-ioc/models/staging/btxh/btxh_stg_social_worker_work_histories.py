"""Explode SocialWorkers.workHistories into sqlmesh_work.btxh_stg_social_worker_work_histories."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import explode_social_worker_work_histories
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "social_worker_id": "text",
    "updated_at": "timestamp",
    "work_history_id": "text",
    "is_current": "boolean",
    "status": "text",
    "start_date": "date",
    "end_date": "date",
    "facility_id": "text",
    "facility_code": "text",
    "facility_name": "text",
    "facility_type": "text",
    "position_id": "text",
    "position_code": "text",
    "position_name": "text",
    "contract_type_id": "text",
    "contract_type_code": "text",
    "contract_type_name": "text",
    "job_description": "text",
}

TIMESTAMP_COLUMNS = ("_airbyte_extracted_at", "updated_at")
DATE_COLUMNS = ("start_date", "end_date")
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
    "sqlmesh_work.btxh_stg_social_worker_work_histories",
    description=(
        "Exploded BTXH social worker work history records from public.\"SocialWorkers\" "
        "with one row per work history item."
    ),
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="updated_at", batch_size=90),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["work_history_id"],
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
                "workHistories"
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
                    records.extend(explode_social_worker_work_histories(dict(row)))

                if records:
                    yield _normalize_dataframe(records)
    finally:
        conn.close()
