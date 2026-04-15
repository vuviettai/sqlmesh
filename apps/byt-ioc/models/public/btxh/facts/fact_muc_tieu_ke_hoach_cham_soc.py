from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_muc_tieu_ke_hoach": "text",
  "ma_ke_hoach_cham_soc": "text",
  "ma_nguoi_thu_huong": "text",
  "ma_ho_so_trung_tam": "text",
  "ma_co_so": "text",
  "ma_dinh_danh_nguon_co_so": "text",
  "ma_muc_tieu_nguon": "text",
  "mo_ta_muc_tieu": "text",
  "muc_do_uu_tien": "text",
  "ma_linh_vuc_danh_gia": "text",
  "nguon": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY objective_id
      ORDER BY updated_at DESC NULLS LAST
    ) AS rn
  FROM {stg_care_plan_objectives}
  WHERE objective_id IS NOT NULL
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.objective_id, ''), 0) & 9223372036854775807)::BIGINT
                                                           AS id,
  d.objective_id::VARCHAR(64)                              AS ma_muc_tieu_ke_hoach,
  d.care_plan_id::VARCHAR(64)                              AS ma_ke_hoach_cham_soc,
  d.beneficiary_id::VARCHAR(64)                            AS ma_nguoi_thu_huong,
  d.center_profile_id::VARCHAR(64)                         AS ma_ho_so_trung_tam,
  d.facility_code::VARCHAR(30)                             AS ma_co_so,
  d.facility_id::VARCHAR(64)                               AS ma_dinh_danh_nguon_co_so,
  d.objective_code::VARCHAR(100)                           AS ma_muc_tieu_nguon,
  d.specific_goal::TEXT                                    AS mo_ta_muc_tieu,
  d.priority_level::VARCHAR(50)                            AS muc_do_uu_tien,
  d.assessment_field_code::VARCHAR(50)                     AS ma_linh_vuc_danh_gia,
  'CARE_ACTIVITIES'::VARCHAR(50)                           AS nguon,
  d.updated_at::DATE                                       AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_muc_tieu_ke_hoach_cham_soc",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_muc_tieu_ke_hoach"),
    owner="data_team",
    cron="@daily",
    grain="ma_muc_tieu_ke_hoach",
    tags=["fact", "btxh", "care_plan", "objective"],
    columns=MODEL_COLUMNS,
    description="BTXH care plan objective fact from CareActivities first-level stream.",
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_care_plan_objectives=context.resolve_table("sqlmesh_work.btxh_stg_care_plan_objectives"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df