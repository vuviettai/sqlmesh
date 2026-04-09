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
  "ma_muc_tieu_phuc_vu": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY facility_code
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_facilities}
  WHERE facility_code IS NOT NULL
    AND NULLIF(service_target_codes, '') IS NOT NULL
),
target_codes AS (
  SELECT
    l.facility_code,
    l.facility_id,
    l.center_type_code,
    l.updated_at,
    NULLIF(BTRIM(code.target_code), '') AS ma_muc_tieu_phuc_vu
  FROM latest l
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(l.service_target_codes, ','))
    AS code(target_code)
  WHERE l.rn = 1
),
deduped AS (
  SELECT *
  FROM target_codes
  WHERE ma_muc_tieu_phuc_vu IS NOT NULL
),
existing_ids AS (
  SELECT ma_co_so, ma_muc_tieu_phuc_vu, id
  FROM public.btxh_fact_muc_tieu_phuc_vu_co_so
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val
  FROM public.btxh_fact_muc_tieu_phuc_vu_co_so
),
new_rows AS (
  SELECT
    d.facility_code,
    d.ma_muc_tieu_phuc_vu,
    ROW_NUMBER() OVER (ORDER BY d.facility_code, d.ma_muc_tieu_phuc_vu) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e
    ON  e.ma_co_so            = d.facility_code
    AND e.ma_muc_tieu_phuc_vu = d.ma_muc_tieu_phuc_vu
  WHERE e.ma_co_so IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT   AS id,
  d.facility_code::VARCHAR(30)                        AS ma_co_so,
  d.facility_id::VARCHAR(64)                          AS ma_dinh_danh_nguon_co_so,
  d.center_type_code::VARCHAR(50)                     AS ma_loai_trung_tam,
  d.ma_muc_tieu_phuc_vu::VARCHAR(50)                  AS ma_muc_tieu_phuc_vu,
  d.updated_at::DATE                                  AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e
  ON  e.ma_co_so            = d.facility_code
  AND e.ma_muc_tieu_phuc_vu = d.ma_muc_tieu_phuc_vu
LEFT JOIN new_rows n
  ON  n.facility_code       = d.facility_code
  AND n.ma_muc_tieu_phuc_vu = d.ma_muc_tieu_phuc_vu
"""


@model(
    name="public.btxh_fact_muc_tieu_phuc_vu_co_so",
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY,
        unique_key=["ma_co_so", "ma_muc_tieu_phuc_vu"],
    ),
    owner="data_team",
    cron="@daily",
    grain=["ma_co_so", "ma_muc_tieu_phuc_vu"],
    tags=["fact", "btxh", "facility", "service_target"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH facility service target fact - one row per facility per "
        "service-target code."
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