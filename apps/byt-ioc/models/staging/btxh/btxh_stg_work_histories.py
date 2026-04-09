"""Transform records from staging_db.WorkHistories into sqlmesh_work.btxh_stg_work_histories."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import flatten_work_history_record
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "work_history_id": "text",
    "su_kien": "text",
    "phien_ban": "bigint",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "social_worker_id": "text",
    "ho_va_ten": "text",
    "email": "text",
    "phone_number": "text",
    "gioi_tinh_ma": "bigint",
    "gioi_tinh": "text",
    "ngay_sinh": "date",
    "ethnicity_code": "text",
    "ethnicity_name": "text",
    "nationality_code": "text",
    "nationality_name": "text",
    "organization_id": "text",
    "document_number": "text",
    "document_type_code": "text",
    "document_type_name": "text",
    "document_issue_date": "date",
    "document_issue_place": "text",
    "current_address": "text",
    "current_ward_id": "text",
    "current_ward_code": "text",
    "current_ward_name": "text",
    "current_province_id": "text",
    "current_province_code": "text",
    "current_province_name": "text",
    "permanent_address": "text",
    "permanent_ward_id": "text",
    "permanent_ward_code": "text",
    "permanent_ward_name": "text",
    "permanent_province_id": "text",
    "permanent_province_code": "text",
    "permanent_province_name": "text",
    "status": "text",
    "is_current": "boolean",
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

TIMESTAMP_COLUMNS = ("_airbyte_extracted_at", "created_at", "updated_at")
DATE_COLUMNS = ("ngay_sinh", "document_issue_date", "start_date", "end_date")
INTEGER_COLUMNS = ("_airbyte_generation_id", "phien_ban", "gioi_tinh_ma")
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
    "sqlmesh_work.btxh_stg_work_histories",
    description=(
        "Cleaned and flattened BTXH work history records from the staging "
        'PostgreSQL table public."WorkHistories" into the BI database.'
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
        table_name = os.environ.get("STAGING_BTXH_WORK_HISTORY_SOURCE_TABLE", "WorkHistories")
        query = sql.SQL(
            """
            SELECT
                _airbyte_raw_id,
                _airbyte_extracted_at,
                _airbyte_generation_id,
                id,
                "suKien",
                "phienBan",
                "createdAt",
                "updatedAt",
                "createdAtmm",
                "updatedAtmm",
                "workHistory",
                "socialWorker"
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

                records = [flatten_work_history_record(dict(row)) for row in rows]
                yield _normalize_dataframe(records)
    finally:
        conn.close()