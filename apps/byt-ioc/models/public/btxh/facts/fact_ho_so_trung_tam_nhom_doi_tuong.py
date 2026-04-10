from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_ho_so_trung_tam": "text",
  "ma_nguoi_thu_huong": "text",
  "ma_co_so": "text",
  "ma_nhom_doi_tuong_chinh": "text",
  "ma_nhom_doi_tuong": "text",
  "ma_chi_tiet_doi_tuong": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY center_profile_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_center_profiles}
  WHERE center_profile_id IS NOT NULL
    AND beneficiary_id    IS NOT NULL
    AND ma_co_so          IS NOT NULL
    AND NULLIF(ma_nhom_doi_tuong, '') IS NOT NULL
),
deduped AS (
  SELECT
    l.center_profile_id,
    l.beneficiary_id,
    l.ma_co_so,
    l.ma_nhom_doi_tuong_chinh,
    NULLIF(BTRIM(t.group_code), '')  AS ma_nhom_doi_tuong,
    NULLIF(BTRIM(t.detail_code), '') AS ma_chi_tiet_doi_tuong,
    l.updated_at
  FROM latest l
  CROSS JOIN LATERAL UNNEST(
    STRING_TO_ARRAY(l.ma_nhom_doi_tuong, ','),
    STRING_TO_ARRAY(COALESCE(l.ma_chi_tiet_doi_tuong, ''), ',')
  ) AS t(group_code, detail_code)
  WHERE l.rn = 1
    AND NULLIF(BTRIM(t.group_code), '') IS NOT NULL
)
SELECT
  (
    HASHTEXTEXTENDED(CONCAT_WS('||', COALESCE(d.center_profile_id, ''), COALESCE(d.ma_nhom_doi_tuong, '')), 0)
    & 9223372036854775807
  )::BIGINT                                            AS id,
  d.center_profile_id::VARCHAR(64)                    AS ma_ho_so_trung_tam,
  d.beneficiary_id::VARCHAR(64)                       AS ma_nguoi_thu_huong,
  d.ma_co_so::VARCHAR(30)                             AS ma_co_so,
  d.ma_nhom_doi_tuong_chinh::VARCHAR(50)              AS ma_nhom_doi_tuong_chinh,
  d.ma_nhom_doi_tuong::VARCHAR(50)                    AS ma_nhom_doi_tuong,
  d.ma_chi_tiet_doi_tuong::VARCHAR(100)               AS ma_chi_tiet_doi_tuong,
  d.updated_at::DATE                                  AS ngay_cap_nhat
FROM deduped d
"""


@model(
    name="public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong",
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY,
        unique_key=["ma_ho_so_trung_tam", "ma_nhom_doi_tuong"],
    ),
    owner="data_team",
    cron="@daily",
    grain=["ma_ho_so_trung_tam", "ma_nhom_doi_tuong"],
    tags=["fact", "btxh", "center_stay", "object_type"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH object-type-group assignment fact - one row per center profile per "
        "object type group code."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_center_profiles=context.resolve_table("sqlmesh_work.btxh_stg_center_profiles"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df