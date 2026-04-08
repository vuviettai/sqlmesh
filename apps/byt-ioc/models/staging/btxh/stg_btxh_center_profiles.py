"""Explode Beneficiaries.centerProfiles into sqlmesh_work.stg_btxh_center_profiles."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import explode_beneficiary_center_profiles
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "beneficiary_id": "text",
    "updated_at": "timestamp",
    "center_profile_id": "text",
    "profile_active": "boolean",
    "profile_deleted": "boolean",
    "ma_trang_thai_ho_so": "text",
    "ma_co_so": "text",
    "ten_co_so": "text",
    "facility_id": "text",
    "loai_luu_tru": "text",
    "ngay_tiep_nhan": "date",
    "ngay_quyet_dinh_tiep_nhan": "date",
    "so_quyet_dinh_tiep_nhan": "text",
    "co_so_ban_hanh_quyet_dinh": "text",
    "so_quyet_dinh": "text",
    "ma_nhom_doi_tuong_chinh": "text",
    "ma_nhom_doi_tuong": "text",
    "ma_chi_tiet_doi_tuong": "text",
    "ma_dich_vu": "text",
    "ten_dich_vu": "text",
    "so_phong": "text",
}

TIMESTAMP_COLUMNS = (
    "_airbyte_extracted_at",
    "updated_at",
)

DATE_COLUMNS = (
    "ngay_tiep_nhan",
    "ngay_quyet_dinh_tiep_nhan",
)

INTEGER_COLUMNS = (
    "_airbyte_generation_id",
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
    "sqlmesh_work.stg_btxh_center_profiles",
    description=(
        "Exploded BTXH center-profile records from public.\"Beneficiaries\" "
        "with one row per beneficiary center profile."
    ),
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        time_column="updated_at",
        batch_size=90,
    ),
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
                \"updatedAt\",
                \"updatedAtmm\",
                \"centerProfiles\"
            FROM {schema}.{table}
            WHERE COALESCE(
                TO_TIMESTAMP(\"updatedAt\" / 1000.0),
                TO_TIMESTAMP(NULLIF(\"updatedAtmm\", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
            ) >= %(start)s
              AND COALESCE(
                TO_TIMESTAMP(\"updatedAt\" / 1000.0),
                TO_TIMESTAMP(NULLIF(\"updatedAtmm\", ''), 'YYYYMMDDHH24MISS'),
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

                records: list[dict[str, t.Any]] = []
                for row in rows:
                    records.extend(explode_beneficiary_center_profiles(dict(row)))

                if records:
                    yield _normalize_dataframe(records)
    finally:
        conn.close()