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
  "ma_dich_vu": "text",
  "ten_dich_vu": "text",
  "ngay_tiep_nhan": "date",
  "ngay_quyet_dinh_tiep_nhan": "date",
  "trang_thai_ho_so": "text",
  "loai_luu_tru": "text",
  "ho_so_dang_hoat_dong": "boolean",
  "ho_so_da_xoa": "boolean",
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
    AND beneficiary_id IS NOT NULL
    AND ma_co_so IS NOT NULL
    AND NULLIF(ma_dich_vu, '') IS NOT NULL
),
deduped AS (
  SELECT
    l.center_profile_id,
    l.beneficiary_id,
    l.ma_co_so,
    NULLIF(BTRIM(t.service_code), '')                         AS ma_dich_vu,
    COALESCE(NULLIF(BTRIM(t.service_name), ''), 'KHONG_XAC_DINH')::VARCHAR(255) AS ten_dich_vu,
    l.ngay_tiep_nhan,
    l.ngay_quyet_dinh_tiep_nhan,
    l.ma_trang_thai_ho_so,
    l.loai_luu_tru,
    l.profile_active,
    l.profile_deleted,
    l.updated_at
  FROM latest l
  CROSS JOIN LATERAL UNNEST(
    STRING_TO_ARRAY(l.ma_dich_vu, ','),
    STRING_TO_ARRAY(COALESCE(l.ten_dich_vu, ''), ',')
  ) AS t(service_code, service_name)
  WHERE l.rn = 1
    AND NULLIF(BTRIM(t.service_code), '') IS NOT NULL
),
existing_ids AS (
  SELECT ma_ho_so_trung_tam, ma_dich_vu, id
  FROM public.btxh_fact_gan_dich_vu
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val
  FROM public.btxh_fact_gan_dich_vu
),
new_rows AS (
  SELECT
    d.center_profile_id,
    d.ma_dich_vu,
    ROW_NUMBER() OVER (ORDER BY d.center_profile_id, d.ma_dich_vu) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e
    ON  e.ma_ho_so_trung_tam = d.center_profile_id
    AND e.ma_dich_vu         = d.ma_dich_vu
  WHERE e.ma_ho_so_trung_tam IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT         AS id,
  d.center_profile_id::VARCHAR(64)                          AS ma_ho_so_trung_tam,
  d.beneficiary_id::VARCHAR(64)                             AS ma_nguoi_thu_huong,
  d.ma_co_so::VARCHAR(30)                                   AS ma_co_so,
  d.ma_dich_vu::VARCHAR(50)                                 AS ma_dich_vu,
  d.ten_dich_vu::VARCHAR(255)                               AS ten_dich_vu,
  d.ngay_tiep_nhan::DATE                                    AS ngay_tiep_nhan,
  d.ngay_quyet_dinh_tiep_nhan::DATE                         AS ngay_quyet_dinh_tiep_nhan,
  COALESCE(d.ma_trang_thai_ho_so, 'KHONG_XAC_DINH')::VARCHAR(50)
                                                            AS trang_thai_ho_so,
  d.loai_luu_tru::VARCHAR(100)                              AS loai_luu_tru,
  COALESCE(d.profile_active, FALSE)::BOOLEAN                AS ho_so_dang_hoat_dong,
  COALESCE(d.profile_deleted, FALSE)::BOOLEAN               AS ho_so_da_xoa,
  d.updated_at::DATE                                        AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e
  ON  e.ma_ho_so_trung_tam = d.center_profile_id
  AND e.ma_dich_vu         = d.ma_dich_vu
LEFT JOIN new_rows n
  ON  n.center_profile_id  = d.center_profile_id
  AND n.ma_dich_vu         = d.ma_dich_vu
"""


@model(
    name="public.btxh_fact_gan_dich_vu",
    kind=dict(
        name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY,
        unique_key=["ma_ho_so_trung_tam", "ma_dich_vu"],
    ),
    owner="data_team",
    cron="@daily",
    grain=["ma_ho_so_trung_tam", "ma_dich_vu"],
    tags=["fact", "btxh", "service_assignment"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH service assignment fact - one row per center profile and service code."
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