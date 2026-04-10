from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_lich_su_cong_tac": "text",
  "ma_nhan_vien_ctxh": "text",
  "ma_co_so": "text",
  "ten_co_so": "text",
  "loai_co_so": "text",
  "ma_vi_tri": "text",
  "ten_vi_tri": "text",
  "ma_loai_hop_dong": "text",
  "ten_loai_hop_dong": "text",
  "mo_ta_cong_viec": "text",
  "ngay_bat_dau": "date",
  "ngay_ket_thuc": "date",
  "la_cong_tac_hien_tai": "boolean",
  "trang_thai": "text",
  "nguon": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH combined AS (
  SELECT
    work_history_id,
    social_worker_id,
    facility_code,
    facility_name,
    facility_type,
    position_code,
    position_name,
    contract_type_code,
    contract_type_name,
    job_description,
    start_date,
    end_date,
    is_current,
    status,
    updated_at,
    _airbyte_extracted_at,
    'WORK_HISTORIES'  AS nguon
  FROM {stg_work_histories}
  WHERE work_history_id  IS NOT NULL
    AND social_worker_id IS NOT NULL

  UNION ALL

  SELECT
    work_history_id,
    social_worker_id,
    facility_code,
    facility_name,
    facility_type,
    position_code,
    position_name,
    contract_type_code,
    contract_type_name,
    job_description,
    start_date,
    end_date,
    is_current,
    status,
    updated_at,
    _airbyte_extracted_at,
    'SOCIAL_WORKERS'  AS nguon
  FROM {stg_social_worker_work_histories}
  WHERE work_history_id  IS NOT NULL
    AND social_worker_id IS NOT NULL
),
deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY work_history_id
      ORDER BY
        (nguon = 'WORK_HISTORIES') DESC,
        updated_at DESC NULLS LAST,
        _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM combined
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.work_history_id, ''), 0) & 9223372036854775807)::BIGINT
                                                      AS id,
  d.work_history_id::VARCHAR(64)                      AS ma_lich_su_cong_tac,
  d.social_worker_id::VARCHAR(64)                     AS ma_nhan_vien_ctxh,
  d.facility_code::VARCHAR(30)                        AS ma_co_so,
  d.facility_name::VARCHAR(255)                       AS ten_co_so,
  d.facility_type::VARCHAR(50)                        AS loai_co_so,
  d.position_code::VARCHAR(50)                        AS ma_vi_tri,
  d.position_name::VARCHAR(255)                       AS ten_vi_tri,
  d.contract_type_code::VARCHAR(50)                   AS ma_loai_hop_dong,
  d.contract_type_name::VARCHAR(255)                  AS ten_loai_hop_dong,
  d.job_description::TEXT                             AS mo_ta_cong_viec,
  d.start_date::DATE                                  AS ngay_bat_dau,
  d.end_date::DATE                                    AS ngay_ket_thuc,
  COALESCE(d.is_current, FALSE)::BOOLEAN              AS la_cong_tac_hien_tai,
  d.status::VARCHAR(50)                               AS trang_thai,
  d.nguon::VARCHAR(20)                                AS nguon,
  d.updated_at::DATE                                  AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_lich_su_cong_tac_xh",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_lich_su_cong_tac"),
    owner="data_team",
    cron="@daily",
    grain="ma_lich_su_cong_tac",
    tags=["fact", "btxh", "social_worker_work_history"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH social worker work history fact - merged from WorkHistories and "
        "SocialWorkers.workHistories[] streams."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
      QUERY.format(
        stg_work_histories=context.resolve_table("sqlmesh_work.btxh_stg_work_histories"),
        stg_social_worker_work_histories=context.resolve_table(
          "sqlmesh_work.btxh_stg_social_worker_work_histories"
        ),
      )
    )
    if df.empty:
      yield from ()
      return
    yield df