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
)
SELECT
  (
    HASHTEXTEXTENDED(CONCAT_WS('||', COALESCE(d.facility_code, ''), COALESCE(d.ma_muc_tieu_phuc_vu, '')), 0)
    & 9223372036854775807
  )::BIGINT                                            AS id,
  d.facility_code::VARCHAR(30)                        AS ma_co_so,
  d.facility_id::VARCHAR(64)                          AS ma_dinh_danh_nguon_co_so,
  d.center_type_code::VARCHAR(50)                     AS ma_loai_trung_tam,
  d.ma_muc_tieu_phuc_vu::VARCHAR(50)                  AS ma_muc_tieu_phuc_vu,
  d.updated_at::DATE                                  AS ngay_cap_nhat
FROM deduped d
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
            stg_facilities=context.resolve_table("sqlmesh_work.btxh_stg_facilities"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df