"""Explode Beneficiaries.centerProfiles[].familyInfo into sqlmesh_work.btxh_stg_center_profile_family_info."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import explode_center_profile_family_info
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "beneficiary_id": "text",
    "center_profile_id": "text",
    "facility_id": "text",
    "facility_code": "text",
    "updated_at": "timestamp",
    "family_info_id": "text",
    "guardian_id": "text",
    "guardian_full_name": "text",
    "guardian_gender": "text",
    "guardian_phone": "text",
    "guardian_relationship_code": "text",
    "guardian_ward_code": "text",
    "guardian_province_code": "text",
    "household_head_full_name": "text",
    "household_head_gender": "text",
    "household_head_phone": "text",
    "household_head_relationship_code": "text",
    "income_cash": "double",
    "income_kind": "text",
    "other_social_assistance": "text",
    "total_family_members": "bigint",
    "total_main_working_members": "bigint",
    "policy_benefit_count": "bigint",
    "poverty_decision_count": "bigint",
}

TIMESTAMP_COLUMNS = ("_airbyte_extracted_at", "updated_at")
INTEGER_COLUMNS = (
    "_airbyte_generation_id",
    "total_family_members",
    "total_main_working_members",
    "policy_benefit_count",
    "poverty_decision_count",
)
FLOAT_COLUMNS = ("income_cash",)
FETCH_BATCH_SIZE = 5_000


def _normalize_dataframe(records: list[dict[str, t.Any]]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records)
    df = df.reindex(columns=MODEL_COLUMNS.keys())

    for col in TIMESTAMP_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in INTEGER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in FLOAT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.astype(object).where(pd.notna(df), None)


@model(
    "sqlmesh_work.btxh_stg_center_profile_family_info",
    description=(
        "Exploded BTXH center-profile family info from public.\"Beneficiaries\" "
        "with one row per center profile having familyInfo."
    ),
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="updated_at", batch_size=90),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["center_profile_id"],
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
        table_name = os.environ.get("STAGING_BTXH_SOURCE_TABLE", "Beneficiaries")
        query = sql.SQL(
            """
            SELECT
                _airbyte_raw_id,
                _airbyte_extracted_at,
                _airbyte_generation_id,
                id,
                "updatedAtmm",
                "centerProfile"
            FROM {schema}.{table}
            WHERE COALESCE(
                TO_TIMESTAMP(NULLIF("updatedAtmm", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
            ) >= %(start)s
              AND COALESCE(
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
                    records.extend(explode_center_profile_family_info(dict(row)))

                if records:
                    yield _normalize_dataframe(records)
    finally:
        conn.close()