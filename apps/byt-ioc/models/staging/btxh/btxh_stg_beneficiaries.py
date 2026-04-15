"""Transform records from staging_db.Beneficiaries into sqlmesh_work.btxh_stg_beneficiaries."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .btxh_helper import flatten_beneficiary
from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "beneficiary_id": "text",
    "is_active": "boolean",
    "gioi_tinh_ma": "bigint",
    "gioi_tinh": "text",
    "su_kien": "text",
    "ho_va_ten": "text",
    "phien_ban": "bigint",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "created_at_nguon": "text",
    "updated_at_nguon": "text",
    "ngay_sinh": "date",
    "dan_toc": "text",
    "quoc_tich": "text",
    "noi_sinh": "text",
    "so_giay_to": "text",
    "ma_loai_giay_to": "text",
    "noi_cap_giay_to": "text",
    "ngay_cap_giay_to": "timestamp",
    "dia_chi_hien_tai": "text",
    "ma_xa_hien_tai": "text",
    "ma_tinh_hien_tai": "text",
    "dia_chi_moi": "text",
    "ma_xa_moi": "text",
    "ma_tinh_moi": "text",
    "co_ho_so_trung_tam": "boolean",
    "so_ho_so_trung_tam": "bigint",
    "so_ho_so_trung_tam_hoat_dong": "bigint",
    "center_profile_id": "text",
    "ma_co_so_hien_tai": "text",
    "ten_co_so_hien_tai": "text",
    "facility_id": "text",
    "ma_trang_thai_ho_so": "text",
    "loai_luu_tru": "text",
    "ngay_tiep_nhan": "date",
    "ngay_quyet_dinh_tiep_nhan": "date",
    "so_quyet_dinh_tiep_nhan": "text",
    "co_so_ban_hanh_quyet_dinh": "text",
    "ma_nhom_doi_tuong_chinh": "text",
    "danh_sach_ma_nhom_doi_tuong": "text",
    "danh_sach_ma_dich_vu": "text",
    "danh_sach_dich_vu": "text",
}

TIMESTAMP_COLUMNS = ("_airbyte_extracted_at", "created_at", "updated_at", "ngay_cap_giay_to")
DATE_COLUMNS = ("ngay_sinh", "ngay_tiep_nhan", "ngay_quyet_dinh_tiep_nhan")
INTEGER_COLUMNS = ("_airbyte_generation_id", "gioi_tinh_ma", "phien_ban", "so_ho_so_trung_tam", "so_ho_so_trung_tam_hoat_dong")
FETCH_BATCH_SIZE = 10_000


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
    "sqlmesh_work.btxh_stg_beneficiaries",
    description=(
        "Cleaned and flattened BTXH beneficiary records from the staging "
        'PostgreSQL table public."Beneficiaries" into the BI database.'
    ),
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="updated_at", batch_size=90),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["_airbyte_raw_id"],
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
                gender,
                \"suKien\",
                \"fullName\",
                \"phienBan\",
                ethnicity,
                residence,
                \"createdAtmm\",
                \"dateOfBirth\",
                nationality,
                \"updatedAtmm\",
                \"paperIdentity\",
                \"placeOfOrigin\",
                \"centerProfile\"
            FROM {schema}.{table}
            WHERE COALESCE(
                TO_TIMESTAMP(NULLIF(\"updatedAtmm\", ''), 'YYYYMMDDHH24MISS'),
                _airbyte_extracted_at
            ) >= %(start)s
              AND COALESCE(
                TO_TIMESTAMP(NULLIF(\"updatedAtmm\", ''), 'YYYYMMDDHH24MISS'),
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

                records = [flatten_beneficiary(dict(row)) for row in rows]
                yield _normalize_dataframe(records)
    finally:
        conn.close()
