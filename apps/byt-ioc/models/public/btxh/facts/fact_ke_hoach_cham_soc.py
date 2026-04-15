from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_ke_hoach_cham_soc": "text",
  "ma_nguoi_thu_huong": "text",
  "ma_ho_so_trung_tam": "text",
  "ma_co_so": "text",
  "ma_dinh_danh_nguon_co_so": "text",
  "trang_thai_ke_hoach_cham_soc": "text",
  "ngay_lap_ke_hoach": "date",
  "ngay_bat_dau": "date",
  "ngay_ket_thuc": "date",
  "ngay_phe_duyet": "date",
  "ngay_ra_soat": "date",
  "so_ke_hoach": "text",
  "ma_nguoi_quan_ly": "text",
  "doi_tuong_hoac_nguoi_giam_ho": "text",
  "ten_lanh_dao_co_so": "text",
  "danh_sach_don_vi_thuc_hien": "text",
  "so_don_vi_thuc_hien": "int",
  "nguon": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY care_plan_id
      ORDER BY updated_at DESC NULLS LAST
    ) AS rn
  FROM {stg_care_plans}
  WHERE care_plan_id IS NOT NULL
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.care_plan_id, ''), 0) & 9223372036854775807)::BIGINT
                                                           AS id,
  d.care_plan_id::VARCHAR(64)                              AS ma_ke_hoach_cham_soc,
  d.beneficiary_id::VARCHAR(64)                            AS ma_nguoi_thu_huong,
  d.center_profile_id::VARCHAR(64)                         AS ma_ho_so_trung_tam,
  d.facility_code::VARCHAR(30)                             AS ma_co_so,
  d.facility_id::VARCHAR(64)                               AS ma_dinh_danh_nguon_co_so,
  COALESCE(d.care_plan_status, 'KHONG_XAC_DINH')::VARCHAR(50)
                                                           AS trang_thai_ke_hoach_cham_soc,
  d.plan_date::DATE                                        AS ngay_lap_ke_hoach,
  d.start_date::DATE                                       AS ngay_bat_dau,
  d.end_date::DATE                                         AS ngay_ket_thuc,
  d.approval_date::DATE                                    AS ngay_phe_duyet,
  d.review_date::DATE                                      AS ngay_ra_soat,
  d.plan_number::VARCHAR(100)                              AS so_ke_hoach,
  d.object_manager::VARCHAR(64)                            AS ma_nguoi_quan_ly,
  d.beneficiary_or_guardian::TEXT                          AS doi_tuong_hoac_nguoi_giam_ho,
  d.facility_head_or_chairman::VARCHAR(255)                AS ten_lanh_dao_co_so,
  d.implementing_units::TEXT                               AS danh_sach_don_vi_thuc_hien,
  COALESCE(d.implementing_unit_count, 0)::INT              AS so_don_vi_thuc_hien,
  'CARE_ACTIVITIES'::VARCHAR(50)                           AS nguon,
  d.updated_at::DATE                                       AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_ke_hoach_cham_soc",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_ke_hoach_cham_soc"),
    owner="data_team",
    cron="@daily",
    grain="ma_ke_hoach_cham_soc",
    tags=["fact", "btxh", "care_plan"],
    columns=MODEL_COLUMNS,
    description="BTXH care plan fact from CareActivities first-level stream.",
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_care_plans=context.resolve_table("sqlmesh_work.btxh_stg_care_plans"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df