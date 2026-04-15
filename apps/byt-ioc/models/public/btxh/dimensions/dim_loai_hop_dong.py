from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
    "id": "bigint",
    "ma_loai_hop_dong": "text",
    "ten_loai_hop_dong": "text",
    "ngay_cap_nhat": "date",
}


QUERY = """
WITH all_contract_types AS (
  SELECT contract_type_code AS ma_loai_hop_dong, contract_type_name AS ten_loai_hop_dong, updated_at
  FROM {stg_work_histories}
  WHERE NULLIF(contract_type_code, '') IS NOT NULL
),
deduped AS (
  SELECT
    ma_loai_hop_dong,
    ten_loai_hop_dong,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_loai_hop_dong
      ORDER BY
        (ten_loai_hop_dong IS NOT NULL AND NULLIF(ten_loai_hop_dong, '') IS NOT NULL) DESC,
        updated_at DESC NULLS LAST
    ) AS rn
  FROM all_contract_types
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.ma_loai_hop_dong, ''), 0) & 9223372036854775807)::BIGINT AS id,
  d.ma_loai_hop_dong::VARCHAR(50) AS ma_loai_hop_dong,
  COALESCE(NULLIF(d.ten_loai_hop_dong, ''), 'KHONG_XAC_DINH')::VARCHAR(255) AS ten_loai_hop_dong,
  d.updated_at::DATE AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_loai_hop_dong",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain="ma_loai_hop_dong",
    tags=["dimension", "btxh", "reference"],
    columns=MODEL_COLUMNS,
    description=(
      "BTXH contract type dimension - distinct contract type codes from WorkHistories."
    ),
)
def execute(context: ExecutionContext, **kwargs: t.Any) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_work_histories=context.resolve_table("sqlmesh_work.btxh_stg_work_histories"),
        )
    )

    if df.empty:
        yield from ()
        return

    yield df