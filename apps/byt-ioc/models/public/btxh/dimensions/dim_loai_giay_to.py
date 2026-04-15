from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_loai_giay_to": "text",
  "ten_loai_giay_to": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH all_doc_types AS (
  SELECT document_type_code AS ma_loai_giay_to, document_type_name AS ten_loai_giay_to, updated_at
  FROM {stg_social_workers}
  WHERE NULLIF(document_type_code, '') IS NOT NULL

  UNION ALL

  SELECT document_type_code AS ma_loai_giay_to, document_type_name AS ten_loai_giay_to, updated_at
  FROM {stg_work_histories}
  WHERE NULLIF(document_type_code, '') IS NOT NULL

  UNION ALL

  SELECT ma_loai_giay_to AS ma_loai_giay_to, NULL AS ten_loai_giay_to, updated_at
  FROM {stg_beneficiaries}
  WHERE NULLIF(ma_loai_giay_to, '') IS NOT NULL
),
deduped AS (
  SELECT
    ma_loai_giay_to,
    ten_loai_giay_to,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_loai_giay_to
      ORDER BY
        (ten_loai_giay_to IS NOT NULL AND NULLIF(ten_loai_giay_to, '') IS NOT NULL) DESC,
        updated_at DESC NULLS LAST
    ) AS rn
  FROM all_doc_types
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.ma_loai_giay_to, ''), 0) & 9223372036854775807)::BIGINT
                                                             AS id,
  d.ma_loai_giay_to::VARCHAR(20)                             AS ma_loai_giay_to,
  COALESCE(NULLIF(d.ten_loai_giay_to, ''), 'KHONG_XAC_DINH')::VARCHAR(100)
                                                             AS ten_loai_giay_to,
  d.updated_at::DATE                                         AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_loai_giay_to",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain="ma_loai_giay_to",
    tags=["dimension", "btxh", "reference"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH document type dimension - distinct identity document type codes "
        "observed across beneficiaries and social workers."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    try:
        stg_social_workers = context.resolve_table("sqlmesh_work.btxh_stg_social_workers")
    except KeyError:
        stg_social_workers = '"sqlmesh_work"."btxh_stg_social_workers"'

    try:
        stg_work_histories = context.resolve_table("sqlmesh_work.btxh_stg_work_histories")
    except KeyError:
        stg_work_histories = '"sqlmesh_work"."btxh_stg_work_histories"'

    try:
        stg_beneficiaries = context.resolve_table("sqlmesh_work.btxh_stg_beneficiaries")
    except KeyError:
        stg_beneficiaries = '"sqlmesh_work"."btxh_stg_beneficiaries"'

    df = context.fetchdf(
        QUERY.format(
            stg_social_workers=stg_social_workers,
            stg_work_histories=stg_work_histories,
            stg_beneficiaries=stg_beneficiaries,
        )
    )
    if df.empty:
        yield from ()
        return
    yield df