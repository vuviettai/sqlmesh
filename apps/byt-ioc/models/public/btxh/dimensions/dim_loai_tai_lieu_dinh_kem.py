from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "ma_loai_tai_lieu": "text",
  "ten_loai_tai_lieu": "text",
  "nguon": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH all_types AS (
  SELECT
    NULLIF(attachment_type, '') AS ma_loai_tai_lieu,
    NULLIF(attachment_type, '') AS ten_loai_tai_lieu,
    'BENEFICIARY_ATTACHMENTS'::TEXT AS nguon,
    updated_at
  FROM {stg_beneficiary_attachments}
  WHERE NULLIF(attachment_type, '') IS NOT NULL

  UNION ALL

  SELECT
    NULLIF(document_type, '') AS ma_loai_tai_lieu,
    NULLIF(document_type, '') AS ten_loai_tai_lieu,
    'SOCIAL_WORKER_DOCUMENTS'::TEXT AS nguon,
    updated_at
  FROM {stg_social_worker_documents}
  WHERE NULLIF(document_type, '') IS NOT NULL
),
deduped AS (
  SELECT
    ma_loai_tai_lieu,
    ten_loai_tai_lieu,
    nguon,
    updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY ma_loai_tai_lieu, nguon
      ORDER BY updated_at DESC NULLS LAST
    ) AS rn
  FROM all_types
)
SELECT
  d.ma_loai_tai_lieu::VARCHAR(100)                             AS ma_loai_tai_lieu,
  COALESCE(d.ten_loai_tai_lieu, 'KHONG_XAC_DINH')::VARCHAR(255)
                                                               AS ten_loai_tai_lieu,
  d.nguon::VARCHAR(50)                                         AS nguon,
  d.updated_at::DATE                                           AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_loai_tai_lieu_dinh_kem",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain=["ma_loai_tai_lieu", "nguon"],
    tags=["dimension", "btxh", "attachment"],
    columns=MODEL_COLUMNS,
    description="BTXH attachment/document type dimension from beneficiary and social-worker payloads.",
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_beneficiary_attachments=context.resolve_table("sqlmesh_work.btxh_stg_beneficiary_attachments"),
            stg_social_worker_documents=context.resolve_table("sqlmesh_work.btxh_stg_social_worker_documents"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df