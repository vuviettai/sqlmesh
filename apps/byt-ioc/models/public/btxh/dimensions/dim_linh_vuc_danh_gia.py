from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "ma_linh_vuc_danh_gia": "text",
  "ten_linh_vuc_danh_gia": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH all_codes AS (
  SELECT assessment_field_code AS ma_linh_vuc_danh_gia, updated_at
  FROM {stg_care_plan_objectives}
  WHERE NULLIF(assessment_field_code, '') IS NOT NULL
),
deduped AS (
  SELECT
    ma_linh_vuc_danh_gia,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_linh_vuc_danh_gia
      ORDER BY updated_at DESC NULLS LAST
    ) AS rn
  FROM all_codes
)
SELECT
  d.ma_linh_vuc_danh_gia::VARCHAR(50)                             AS ma_linh_vuc_danh_gia,
  CONCAT('LINH_VUC_', d.ma_linh_vuc_danh_gia)::VARCHAR(255)      AS ten_linh_vuc_danh_gia,
  d.updated_at::DATE                                              AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_linh_vuc_danh_gia",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain="ma_linh_vuc_danh_gia",
    tags=["dimension", "btxh", "care_plan"],
    columns=MODEL_COLUMNS,
    description="BTXH assessment-field dimension from care plan objectives (CareActivities stream).",
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