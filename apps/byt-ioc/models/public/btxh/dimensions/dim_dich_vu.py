from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "ma_dich_vu": "text",
  "ten_dich_vu": "text",
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
  WHERE NULLIF(ma_dich_vu, '') IS NOT NULL
),
service_pairs AS (
  SELECT
    NULLIF(BTRIM(t.service_code), '') AS ma_dich_vu,
    NULLIF(BTRIM(t.service_name), '') AS ten_dich_vu,
    l.updated_at
  FROM latest l
  CROSS JOIN LATERAL UNNEST(
    STRING_TO_ARRAY(l.ma_dich_vu, ','),
    STRING_TO_ARRAY(COALESCE(l.ten_dich_vu, ''), ',')
  ) AS t(service_code, service_name)
  WHERE l.rn = 1
),
deduped AS (
  SELECT
    ma_dich_vu,
    ten_dich_vu,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_dich_vu
      ORDER BY updated_at DESC NULLS LAST, ten_dich_vu DESC NULLS LAST
    ) AS rn
  FROM service_pairs
  WHERE ma_dich_vu IS NOT NULL
)
SELECT
  d.ma_dich_vu::VARCHAR(50)                             AS ma_dich_vu,
  COALESCE(d.ten_dich_vu, 'KHONG_XAC_DINH')::VARCHAR(255)
                                                        AS ten_dich_vu,
  d.updated_at::DATE                                    AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_dich_vu",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain="ma_dich_vu",
    tags=["dimension", "btxh", "service"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH service dimension - distinct service codes and labels observed in "
        "center profiles."
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