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
),
existing_ids AS (
  SELECT ma_ho_so_trung_tam, ma_nhom_doi_tuong, id
  FROM public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val
  FROM public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong
),
new_rows AS (
  SELECT
    d.center_profile_id,
    d.ma_nhom_doi_tuong,
    ROW_NUMBER() OVER (ORDER BY d.center_profile_id, d.ma_nhom_doi_tuong) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e
    ON  e.ma_ho_so_trung_tam = d.center_profile_id
    AND e.ma_nhom_doi_tuong  = d.ma_nhom_doi_tuong
  WHERE e.ma_ho_so_trung_tam IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT   AS id,
  d.center_profile_id::VARCHAR(64)                    AS ma_ho_so_trung_tam,
  d.beneficiary_id::VARCHAR(64)                       AS ma_nguoi_thu_huong,
  d.ma_co_so::VARCHAR(30)                             AS ma_co_so,
  d.ma_nhom_doi_tuong_chinh::VARCHAR(50)              AS ma_nhom_doi_tuong_chinh,
  d.ma_nhom_doi_tuong::VARCHAR(50)                    AS ma_nhom_doi_tuong,
  d.ma_chi_tiet_doi_tuong::VARCHAR(100)               AS ma_chi_tiet_doi_tuong,
  d.updated_at::DATE                                  AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e
  ON  e.ma_ho_so_trung_tam = d.center_profile_id
  AND e.ma_nhom_doi_tuong  = d.ma_nhom_doi_tuong
LEFT JOIN new_rows n
  ON  n.center_profile_id  = d.center_profile_id
  AND n.ma_nhom_doi_tuong  = d.ma_nhom_doi_tuong
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
            stg_center_profiles=context.resolve_table("sqlmesh_work.btxh_stg_center_profiles")
        )
    )
    if df.empty:
        yield from ()
        return
    yield df