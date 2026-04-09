from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "ma_co_so": "text",
  "ten_co_so": "text",
  "ma_dinh_danh_nguon_co_so": "text",
  "ma_loai_trung_tam": "text",
  "ten_loai_trung_tam": "text",
  "ma_hinh_thuc_co_so": "text",
  "ten_hinh_thuc_co_so": "text",
  "ma_don_vi_quan_ly": "text",
  "ten_don_vi_quan_ly": "text",
  "ma_tinh": "text",
  "dia_chi": "text",
  "so_dien_thoai": "text",
  "thu_dien_tu": "text",
  "ten_giam_doc": "text",
  "dang_hoat_dong": "boolean",
  "da_phat_sinh_ho_so": "boolean",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH master_latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY facility_code
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_facilities}
  WHERE facility_code IS NOT NULL
),
observed_latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY ma_co_so
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_center_profiles}
  WHERE ma_co_so IS NOT NULL
),
deduped AS (
  SELECT
    COALESCE(m.facility_code, o.ma_co_so)                                            AS ma_co_so,
    COALESCE(NULLIF(m.facility_name, ''), NULLIF(o.ten_co_so, ''), 'KHONG_XAC_DINH') AS ten_co_so,
    COALESCE(m.facility_id, o.facility_id)                                            AS facility_id,
    COALESCE(m.center_type_code, 'KHONG_XAC_DINH')                                   AS center_type_code,
    COALESCE(m.center_type_name, 'KHONG_XAC_DINH')                                   AS center_type_name,
    COALESCE(m.facility_form, 'KHONG_XAC_DINH')                                      AS facility_form,
    COALESCE(m.facility_form_name, 'KHONG_XAC_DINH')                                 AS facility_form_name,
    m.management_unit_code,
    m.management_unit_name,
    m.province_code,
    m.contact_address,
    COALESCE(m.phone_number, '')                                                      AS phone_number,
    COALESCE(m.email, '')                                                             AS email,
    COALESCE(m.director_name, '')                                                     AS director_name,
    COALESCE(m.is_active, TRUE)                                                       AS is_active,
    (o.ma_co_so IS NOT NULL)                                                          AS da_phat_sinh_ho_so,
    COALESCE(m.updated_at, o.updated_at)                                              AS updated_at
  FROM master_latest m
  FULL OUTER JOIN observed_latest o
    ON o.ma_co_so = m.facility_code
  WHERE COALESCE(m.rn, o.rn) = 1
)
SELECT
  d.ma_co_so::VARCHAR(30)                              AS ma_co_so,
  d.ten_co_so::VARCHAR(255)                            AS ten_co_so,
  d.facility_id::VARCHAR(64)                           AS ma_dinh_danh_nguon_co_so,
  d.center_type_code::VARCHAR(50)                      AS ma_loai_trung_tam,
  d.center_type_name::VARCHAR(255)                     AS ten_loai_trung_tam,
  d.facility_form::VARCHAR(50)                         AS ma_hinh_thuc_co_so,
  d.facility_form_name::VARCHAR(255)                   AS ten_hinh_thuc_co_so,
  d.management_unit_code::VARCHAR(50)                  AS ma_don_vi_quan_ly,
  d.management_unit_name::VARCHAR(255)                 AS ten_don_vi_quan_ly,
  d.province_code::VARCHAR(10)                         AS ma_tinh,
  d.contact_address::TEXT                              AS dia_chi,
  d.phone_number::VARCHAR(50)                          AS so_dien_thoai,
  d.email::VARCHAR(255)                                AS thu_dien_tu,
  d.director_name::VARCHAR(255)                        AS ten_giam_doc,
  d.is_active::BOOLEAN                                 AS dang_hoat_dong,
  d.da_phat_sinh_ho_so::BOOLEAN                        AS da_phat_sinh_ho_so,
  d.updated_at::DATE                                   AS ngay_cap_nhat
FROM deduped d
"""


@model(
    name="public.btxh_dim_co_so",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_co_so"),
    owner="data_team",
    cron="@daily",
    grain="ma_co_so",
    tags=["dimension", "btxh", "facility"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH facility dimension - latest facility master data with fallback to "
        "observed center profile identifiers."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_facilities=context.resolve_table("sqlmesh_work.btxh_stg_facilities"),
            stg_center_profiles=context.resolve_table("sqlmesh_work.btxh_stg_center_profiles"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df