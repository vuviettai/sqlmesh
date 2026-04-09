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
  FROM {stg_social_worker_work_histories}
  WHERE NULLIF(contract_type_code, '') IS NOT NULL

  UNION ALL

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
),
existing_ids AS (
  SELECT ma_loai_hop_dong, id FROM public.btxh_dim_loai_hop_dong
),
max_id AS (
  SELECT COALESCE(MAX(id), 0) AS val FROM public.btxh_dim_loai_hop_dong
),
new_rows AS (
  SELECT
    d.ma_loai_hop_dong,
    ROW_NUMBER() OVER (ORDER BY d.ma_loai_hop_dong) AS seq
  FROM deduped d
  LEFT JOIN existing_ids e ON e.ma_loai_hop_dong = d.ma_loai_hop_dong
  WHERE d.rn = 1
    AND e.ma_loai_hop_dong IS NULL
)
SELECT
  COALESCE(e.id, (SELECT val FROM max_id) + n.seq)::BIGINT AS id,
  d.ma_loai_hop_dong::VARCHAR(50) AS ma_loai_hop_dong,
  COALESCE(NULLIF(d.ten_loai_hop_dong, ''), 'KHONG_XAC_DINH')::VARCHAR(255) AS ten_loai_hop_dong,
  d.updated_at::DATE AS ngay_cap_nhat
FROM deduped d
LEFT JOIN existing_ids e ON e.ma_loai_hop_dong = d.ma_loai_hop_dong
LEFT JOIN new_rows n ON n.ma_loai_hop_dong = d.ma_loai_hop_dong
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
        "BTXH contract type dimension - distinct contract type codes observed "
        "in social worker work histories."
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