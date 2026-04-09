from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_co_so": "text",
  "ma_dinh_danh_nguon_co_so": "text",
  "ma_loai_trung_tam": "text",
  "ma_hinh_thuc_co_so": "text",
  "cong_suat_ke_hoach": "int",
  "tong_nhan_su": "int",
  "tong_doi_tuong": "int",
  "tong_dien_tich": "decimal(18, 2)",
  "dien_tich_binh_quan_mot_doi_tuong": "decimal(18, 2)",
  "dien_tich_nha_o_binh_quan_mot_doi_tuong": "decimal(18, 2)",
  "dang_hoat_dong": "boolean",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY facility_code, updated_at::DATE
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_facilities}
  WHERE facility_code IS NOT NULL
    AND updated_at IS NOT NULL
),
existing_ids AS (
  SELECT ma_co_so, ngay_cap_nhat, id
  FROM public.btxh_fact_nang_luc_co_so
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val
  FROM public.btxh_fact_nang_luc_co_so
),
new_rows AS (
  SELECT
    d.facility_code,
    d.updated_at::DATE AS ngay_cap_nhat,
    ROW_NUMBER() OVER (ORDER BY d.facility_code, d.updated_at::DATE) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e
    ON  e.ma_co_so      = d.facility_code
    AND e.ngay_cap_nhat = d.updated_at::DATE
  WHERE d.rn = 1
    AND e.ma_co_so IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT             AS id,
  d.facility_code::VARCHAR(30)                                  AS ma_co_so,
  d.facility_id::VARCHAR(64)                                    AS ma_dinh_danh_nguon_co_so,
  d.center_type_code::VARCHAR(50)                               AS ma_loai_trung_tam,
  d.facility_form::VARCHAR(50)                                  AS ma_hinh_thuc_co_so,
  NULLIF(REGEXP_REPLACE(d.planned_capacity, '[^0-9.-]', '', 'g'), '')::INT
                                                                AS cong_suat_ke_hoach,
  NULLIF(REGEXP_REPLACE(d.total_staff, '[^0-9.-]', '', 'g'), '')::INT
                                                                AS tong_nhan_su,
  NULLIF(REGEXP_REPLACE(d.total_beneficiaries, '[^0-9.-]', '', 'g'), '')::INT
                                                                AS tong_doi_tuong,
  NULLIF(REGEXP_REPLACE(d.total_area, '[^0-9.-]', '', 'g'), '')::DECIMAL(18, 2)
                                                                AS tong_dien_tich,
  NULLIF(REGEXP_REPLACE(d.avg_area_per_beneficiary, '[^0-9.-]', '', 'g'), '')::DECIMAL(18, 2)
                                                                AS dien_tich_binh_quan_mot_doi_tuong,
  NULLIF(REGEXP_REPLACE(d.avg_housing_area_per_beneficiary, '[^0-9.-]', '', 'g'), '')::DECIMAL(18, 2)
                                                                AS dien_tich_nha_o_binh_quan_mot_doi_tuong,
  COALESCE(d.is_active, TRUE)::BOOLEAN                          AS dang_hoat_dong,
  d.updated_at::DATE                                            AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e
  ON  e.ma_co_so      = d.facility_code
  AND e.ngay_cap_nhat = d.updated_at::DATE
LEFT JOIN new_rows n
  ON  n.facility_code = d.facility_code
  AND n.ngay_cap_nhat = d.updated_at::DATE
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_nang_luc_co_so",
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY,
        unique_key=["ma_co_so", "ngay_cap_nhat"],
    ),
    owner="data_team",
    cron="@daily",
    grain=["ma_co_so", "ngay_cap_nhat"],
    tags=["fact", "btxh", "facility_capacity"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH facility capacity fact - daily facility capacity, staffing, and "
        "occupancy snapshot."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_facilities=context.resolve_table("sqlmesh_work.btxh_stg_facilities")
        )
    )
    if df.empty:
        yield from ()
        return
    yield df