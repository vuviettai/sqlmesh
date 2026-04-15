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
  "ma_dinh_danh_nguon_co_so": "text",
  "ma_thong_tin_gia_dinh": "text",
  "ma_nguoi_giam_ho": "text",
  "ten_nguoi_giam_ho": "text",
  "gioi_tinh_nguoi_giam_ho": "text",
  "dien_thoai_nguoi_giam_ho": "text",
  "ma_quan_he_nguoi_giam_ho": "text",
  "ma_dia_ban_nguoi_giam_ho": "text",
  "ma_tinh_nguoi_giam_ho": "text",
  "ten_chu_ho": "text",
  "gioi_tinh_chu_ho": "text",
  "dien_thoai_chu_ho": "text",
  "ma_quan_he_chu_ho": "text",
  "thu_nhap_tien_mat": "double",
  "loai_thu_nhap": "text",
  "ho_tro_xa_hoi_khac": "text",
  "tong_so_thanh_vien": "bigint",
  "tong_so_lao_dong_chinh": "bigint",
  "so_chinh_sach_huong": "bigint",
  "so_quyet_dinh_ho_ngheo": "bigint",
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
  FROM {stg_center_profile_family_info}
  WHERE center_profile_id IS NOT NULL
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.center_profile_id, ''), 0) & 9223372036854775807)::BIGINT
                                                            AS id,
  d.center_profile_id::VARCHAR(64)                          AS ma_ho_so_trung_tam,
  d.beneficiary_id::VARCHAR(64)                             AS ma_nguoi_thu_huong,
  d.facility_code::VARCHAR(30)                              AS ma_co_so,
  d.facility_id::VARCHAR(64)                                AS ma_dinh_danh_nguon_co_so,
  d.family_info_id::VARCHAR(64)                             AS ma_thong_tin_gia_dinh,
  d.guardian_id::VARCHAR(64)                                AS ma_nguoi_giam_ho,
  d.guardian_full_name::VARCHAR(255)                        AS ten_nguoi_giam_ho,
  d.guardian_gender::VARCHAR(50)                            AS gioi_tinh_nguoi_giam_ho,
  d.guardian_phone::VARCHAR(50)                             AS dien_thoai_nguoi_giam_ho,
  d.guardian_relationship_code::VARCHAR(50)                 AS ma_quan_he_nguoi_giam_ho,
  d.guardian_ward_code::VARCHAR(20)                         AS ma_dia_ban_nguoi_giam_ho,
  d.guardian_province_code::VARCHAR(20)                     AS ma_tinh_nguoi_giam_ho,
  d.household_head_full_name::VARCHAR(255)                  AS ten_chu_ho,
  d.household_head_gender::VARCHAR(50)                      AS gioi_tinh_chu_ho,
  d.household_head_phone::VARCHAR(50)                       AS dien_thoai_chu_ho,
  d.household_head_relationship_code::VARCHAR(50)           AS ma_quan_he_chu_ho,
  d.income_cash::DOUBLE PRECISION                           AS thu_nhap_tien_mat,
  d.income_kind::TEXT                                       AS loai_thu_nhap,
  d.other_social_assistance::TEXT                           AS ho_tro_xa_hoi_khac,
  d.total_family_members::BIGINT                            AS tong_so_thanh_vien,
  d.total_main_working_members::BIGINT                      AS tong_so_lao_dong_chinh,
  d.policy_benefit_count::BIGINT                            AS so_chinh_sach_huong,
  d.poverty_decision_count::BIGINT                          AS so_quyet_dinh_ho_ngheo,
  d.updated_at::DATE                                        AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_ho_so_trung_tam_gia_dinh",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_ho_so_trung_tam"),
    owner="data_team",
    cron="@daily",
    grain="ma_ho_so_trung_tam",
    tags=["fact", "btxh", "center_stay", "family"],
    columns=MODEL_COLUMNS,
    description="BTXH center stay family-context fact from center profile family information.",
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_center_profile_family_info=context.resolve_table(
                "sqlmesh_work.btxh_stg_center_profile_family_info"
            ),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df