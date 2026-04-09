from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
    "id": "bigint",
    "ma_vi_tri": "text",
    "ten_vi_tri": "text",
    "ngay_cap_nhat": "date",
}


QUERY = """
WITH all_positions AS (
  SELECT position_code AS ma_vi_tri, position_name AS ten_vi_tri, updated_at
  FROM {stg_social_worker_work_histories}
  WHERE NULLIF(position_code, '') IS NOT NULL

  UNION ALL

  SELECT position_code AS ma_vi_tri, position_name AS ten_vi_tri, updated_at
  FROM {stg_work_histories}
  WHERE NULLIF(position_code, '') IS NOT NULL
),
deduped AS (
  SELECT
    ma_vi_tri,
    ten_vi_tri,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_vi_tri
      ORDER BY
        (ten_vi_tri IS NOT NULL AND NULLIF(ten_vi_tri, '') IS NOT NULL) DESC,
        updated_at DESC NULLS LAST
    ) AS rn
  FROM all_positions
),
existing_ids AS (
  SELECT ma_vi_tri, id FROM public.btxh_dim_vi_tri_cong_tac
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val FROM public.btxh_dim_vi_tri_cong_tac
),
new_rows AS (
  SELECT
    d.ma_vi_tri,
    ROW_NUMBER() OVER (ORDER BY d.ma_vi_tri) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e ON e.ma_vi_tri = d.ma_vi_tri
  WHERE d.rn = 1
    AND e.ma_vi_tri IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT AS id,
  d.ma_vi_tri::VARCHAR(50) AS ma_vi_tri,
  COALESCE(NULLIF(d.ten_vi_tri, ''), 'KHONG_XAC_DINH')::VARCHAR(255) AS ten_vi_tri,
  d.updated_at::DATE AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e ON e.ma_vi_tri = d.ma_vi_tri
LEFT JOIN new_rows n ON n.ma_vi_tri = d.ma_vi_tri
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_vi_tri_cong_tac",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain="ma_vi_tri",
    tags=["dimension", "btxh", "reference"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH work position dimension - distinct position codes observed in "
        "social worker work histories."
    ),
)
def execute(context: ExecutionContext, **kwargs: t.Any) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_social_worker_work_histories=context.resolve_table(
                "sqlmesh_work.btxh_stg_social_worker_work_histories"
            ),
            stg_work_histories=context.resolve_table("sqlmesh_work.btxh_stg_work_histories"),
        )
    )

    if df.empty:
        yield from ()
        return

    yield df