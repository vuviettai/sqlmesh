"""Transform records from staging_db.CareActivities into sqlmesh_work.btxh_stg_care_activities."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import flatten_care_activity
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "care_activity_id": "text",
    "social_worker_id": "text",
    "beneficiary_id": "text",
    "su_kien": "text",
    "phien_ban": "bigint",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "beneficiary_ho_va_ten": "text",
    "beneficiary_gioi_tinh_ma": "bigint",
    "beneficiary_gioi_tinh": "text",
    "beneficiary_ngay_sinh": "date",
    "beneficiary_quoc_tich": "text",
    "social_worker_ho_va_ten": "text",
    "social_worker_gioi_tinh_ma": "bigint",
    "social_worker_gioi_tinh": "text",
    "social_worker_ngay_sinh": "date",
    "social_worker_quoc_tich": "text",
    "center_profile_id": "text",
    "ma_co_so": "text",
    "ten_co_so": "text",
    "facility_id": "text",
    "care_plan_id": "text",
    "care_plan_status": "text",
    "goal_code": "text",
    "goal_description": "text",
    "priority_level": "text",
    "manager_name": "text",
    "facility_leader_name": "text",
    "responsibility": "text",
    "beneficiary_or_guardian": "text",
    "intervention_activities": "text",
    "assessment_field_code": "text",
    "resources_funding": "text",
    "risks_and_solutions": "text",
    "support_conditions": "text",
    "plan_date": "date",
    "start_date": "date",
    "end_date": "date",
    "approval_date": "date",
    "review_date": "date",
    "plan_number": "text",
    "implementing_units": "text",
    "implementing_unit_count": "bigint",
}

TIMESTAMP_COLUMNS = (
    "_airbyte_extracted_at",
    "created_at",
    "updated_at",
)

DATE_COLUMNS = (
    "beneficiary_ngay_sinh",
    "social_worker_ngay_sinh",
    "plan_date",
    "start_date",
    "end_date",
    "approval_date",
    "review_date",
)

INTEGER_COLUMNS = (
    "_airbyte_generation_id",
    "phien_ban",
    "beneficiary_gioi_tinh_ma",
    "social_worker_gioi_tinh_ma",
    "implementing_unit_count",
)

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
    "sqlmesh_work.btxh_stg_care_activities",
    description=(
        "Cleaned and flattened BTXH care activity records from the staging "
        'PostgreSQL table public."CareActivities" into the BI database.'
    ),
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        time_column="updated_at",
        batch_size=90,
    ),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["care_activity_id"],
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
        table_name = os.environ.get("STAGING_BTXH_CARE_ACTIVITY_SOURCE_TABLE", "CareActivities")
        query = sql.SQL(
            """
            SELECT
                _airbyte_raw_id,
                _airbyte_extracted_at,
                _airbyte_generation_id,
                id,
                person,
                \"suKien\",
                \"carePlan\",
                \"phienBan\",
                \"createdAtmm\",
                \"updatedAtmm\"
            FROM {schema}.{table}
            WHERE COALESCE(
                TO_TIMESTAMP(NULLIF(\"updatedAtmm\", ''), 'YYYYMMDDHH24MISS'),
                TO_TIMESTAMP(NULLIF(\"createdAtmm\", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
            ) >= %(start)s
              AND COALESCE(
                TO_TIMESTAMP(NULLIF(\"updatedAtmm\", ''), 'YYYYMMDDHH24MISS'),
                TO_TIMESTAMP(NULLIF(\"createdAtmm\", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
              ) < %(end)s
            """
        ).format(
            schema=sql.Identifier(schema_name),
            table=sql.Identifier(table_name),
        )

        with conn.cursor() as cur:
            cur.execute(query, {"start": start, "end": end})
            while True:
                rows = cur.fetchmany(FETCH_BATCH_SIZE)
                if not rows:
                    break

                records = [flatten_care_activity(dict(row)) for row in rows]
                yield _normalize_dataframe(records)
    finally:
        conn.close()