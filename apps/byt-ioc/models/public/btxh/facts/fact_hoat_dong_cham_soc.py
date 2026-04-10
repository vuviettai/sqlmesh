from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_hoat_dong_cham_soc": "text",
  "ma_nguoi_thu_huong": "text",
  "ma_co_so": "text",
  "ma_ke_hoach_cham_soc": "text",
  "trang_thai_ke_hoach_cham_soc": "text",
  "ma_muc_tieu": "text",
  "mo_ta_muc_tieu": "text",
  "muc_do_uu_tien": "text",
  "ten_nguoi_quan_ly": "text",
  "ten_lanh_dao_co_so": "text",
  "trach_nhiem": "text",
  "doi_tuong_hoac_nguoi_giam_ho": "text",
  "hoat_dong_can_thiep": "text",
  "ma_linh_vuc_danh_gia": "text",
  "nguon_luc_kinh_phi": "text",
  "rui_ro_va_giai_phap": "text",
  "dieu_kien_ho_tro": "text",
  "ngay_lap_ke_hoach": "date",
  "ngay_bat_dau": "date",
  "ngay_ket_thuc": "date",
  "ngay_phe_duyet": "date",
  "ngay_ra_soat": "date",
  "so_ke_hoach": "text",
  "danh_sach_don_vi_thuc_hien": "text",
  "so_don_vi_thuc_hien": "int",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY care_activity_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_care_activities}
  WHERE care_activity_id IS NOT NULL
    AND beneficiary_id IS NOT NULL
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.care_activity_id, ''), 0) & 9223372036854775807)::BIGINT
                                                            AS id,
  d.care_activity_id::VARCHAR(64)                           AS ma_hoat_dong_cham_soc,
  d.beneficiary_id::VARCHAR(64)                             AS ma_nguoi_thu_huong,
  d.ma_co_so::VARCHAR(30)                                   AS ma_co_so,
  d.care_plan_id::VARCHAR(64)                               AS ma_ke_hoach_cham_soc,
  COALESCE(d.care_plan_status, 'KHONG_XAC_DINH')::VARCHAR(50)
                                                            AS trang_thai_ke_hoach_cham_soc,
  d.goal_code::VARCHAR(50)                                  AS ma_muc_tieu,
  d.goal_description::TEXT                                  AS mo_ta_muc_tieu,
  d.priority_level::VARCHAR(50)                             AS muc_do_uu_tien,
  d.manager_name::VARCHAR(255)                              AS ten_nguoi_quan_ly,
  d.facility_leader_name::VARCHAR(255)                      AS ten_lanh_dao_co_so,
  d.responsibility::TEXT                                    AS trach_nhiem,
  d.beneficiary_or_guardian::TEXT                           AS doi_tuong_hoac_nguoi_giam_ho,
  d.intervention_activities::TEXT                           AS hoat_dong_can_thiep,
  d.assessment_field_code::VARCHAR(50)                      AS ma_linh_vuc_danh_gia,
  d.resources_funding::TEXT                                 AS nguon_luc_kinh_phi,
  d.risks_and_solutions::TEXT                               AS rui_ro_va_giai_phap,
  d.support_conditions::TEXT                                AS dieu_kien_ho_tro,
  d.plan_date::DATE                                         AS ngay_lap_ke_hoach,
  d.start_date::DATE                                        AS ngay_bat_dau,
  d.end_date::DATE                                          AS ngay_ket_thuc,
  d.approval_date::DATE                                     AS ngay_phe_duyet,
  d.review_date::DATE                                       AS ngay_ra_soat,
  d.plan_number::VARCHAR(100)                               AS so_ke_hoach,
  d.implementing_units::TEXT                                AS danh_sach_don_vi_thuc_hien,
  COALESCE(d.implementing_unit_count, 0)::INT               AS so_don_vi_thuc_hien,
  d.updated_at::DATE                                        AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_hoat_dong_cham_soc",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_hoat_dong_cham_soc"),
    owner="data_team",
    cron="@daily",
    grain="ma_hoat_dong_cham_soc",
    tags=["fact", "btxh", "care_activity"],
    columns=MODEL_COLUMNS,
    description="BTXH care activity fact - one row per care activity / care plan record.",
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_care_activities=context.resolve_table("sqlmesh_work.btxh_stg_care_activities"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df