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
  "ngay_tiep_nhan": "date",
  "ngay_quyet_dinh_tiep_nhan": "date",
  "so_quyet_dinh_tiep_nhan": "text",
  "co_so_ban_hanh_quyet_dinh": "text",
  "so_quyet_dinh": "text",
  "trang_thai_ho_so": "text",
  "loai_luu_tru": "text",
  "ma_nhom_doi_tuong_chinh": "text",
  "danh_sach_ma_nhom_doi_tuong": "text",
  "danh_sach_ma_chi_tiet_doi_tuong": "text",
  "danh_sach_ma_dich_vu": "text",
  "danh_sach_dich_vu": "text",
  "ho_so_dang_hoat_dong": "boolean",
  "ho_so_da_xoa": "boolean",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
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
),
existing_ids AS (
  SELECT ma_ho_so_trung_tam, id
  FROM public.btxh_fact_ho_so_trung_tam
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val
  FROM public.btxh_fact_ho_so_trung_tam
),
new_rows AS (
  SELECT
    d.center_profile_id,
    ROW_NUMBER() OVER (ORDER BY d.center_profile_id) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e ON e.ma_ho_so_trung_tam = d.center_profile_id
  WHERE d.rn = 1
    AND e.ma_ho_so_trung_tam IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT   AS id,
  d.center_profile_id::VARCHAR(64)                    AS ma_ho_so_trung_tam,
  d.beneficiary_id::VARCHAR(64)                       AS ma_nguoi_thu_huong,
  d.ma_co_so::VARCHAR(30)                             AS ma_co_so,
  d.ngay_tiep_nhan::DATE                              AS ngay_tiep_nhan,
  d.ngay_quyet_dinh_tiep_nhan::DATE                   AS ngay_quyet_dinh_tiep_nhan,
  d.so_quyet_dinh_tiep_nhan::VARCHAR(100)             AS so_quyet_dinh_tiep_nhan,
  d.co_so_ban_hanh_quyet_dinh::VARCHAR(255)           AS co_so_ban_hanh_quyet_dinh,
  d.so_quyet_dinh::VARCHAR(100)                       AS so_quyet_dinh,
  COALESCE(d.ma_trang_thai_ho_so, 'KHONG_XAC_DINH')::VARCHAR(50)
                                                      AS trang_thai_ho_so,
  d.loai_luu_tru::VARCHAR(100)                        AS loai_luu_tru,
  d.ma_nhom_doi_tuong_chinh::VARCHAR(50)              AS ma_nhom_doi_tuong_chinh,
  d.ma_nhom_doi_tuong::TEXT                           AS danh_sach_ma_nhom_doi_tuong,
  d.ma_chi_tiet_doi_tuong::TEXT                       AS danh_sach_ma_chi_tiet_doi_tuong,
  d.ma_dich_vu::TEXT                                  AS danh_sach_ma_dich_vu,
  d.ten_dich_vu::TEXT                                 AS danh_sach_dich_vu,
  COALESCE(d.profile_active, FALSE)::BOOLEAN          AS ho_so_dang_hoat_dong,
  COALESCE(d.profile_deleted, FALSE)::BOOLEAN         AS ho_so_da_xoa,
  d.updated_at::DATE                                  AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e ON e.ma_ho_so_trung_tam = d.center_profile_id
LEFT JOIN new_rows     n ON n.center_profile_id   = d.center_profile_id
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_ho_so_trung_tam",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_ho_so_trung_tam"),
    owner="data_team",
    cron="@daily",
    grain="ma_ho_so_trung_tam",
    tags=["fact", "btxh", "center_stay"],
    columns=MODEL_COLUMNS,
    description="BTXH center stay fact - one row per beneficiary center profile.",
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