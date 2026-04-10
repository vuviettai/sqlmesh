from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_dan_toc": "text",
  "ten_dan_toc": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH all_ethnicities AS (
  SELECT ethnicity_code AS ma_dan_toc, ethnicity_name AS ten_dan_toc, updated_at
  FROM {stg_social_workers}
  WHERE NULLIF(ethnicity_code, '') IS NOT NULL

  UNION ALL

  SELECT ethnicity_code AS ma_dan_toc, ethnicity_name AS ten_dan_toc, updated_at
  FROM {stg_work_histories}
  WHERE NULLIF(ethnicity_code, '') IS NOT NULL
),
deduped AS (
  SELECT
    ma_dan_toc,
    ten_dan_toc,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_dan_toc
      ORDER BY
        (ten_dan_toc IS NOT NULL AND NULLIF(ten_dan_toc, '') IS NOT NULL) DESC,
        updated_at DESC NULLS LAST
    ) AS rn
  FROM all_ethnicities
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.ma_dan_toc, ''), 0) & 9223372036854775807)::BIGINT
                                                             AS id,
  d.ma_dan_toc::VARCHAR(20)                                  AS ma_dan_toc,
  COALESCE(NULLIF(d.ten_dan_toc, ''), 'KHONG_XAC_DINH')::VARCHAR(100)
                                                             AS ten_dan_toc,
  d.updated_at::DATE                                         AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_dan_toc",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain="ma_dan_toc",
    tags=["dimension", "btxh", "reference"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH ethnicity dimension - distinct ethnicity codes observed across "
        "social workers and work histories."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_social_workers=context.resolve_table("sqlmesh_work.btxh_stg_social_workers"),
            stg_work_histories=context.resolve_table("sqlmesh_work.btxh_stg_work_histories"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df