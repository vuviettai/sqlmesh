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
SELECT
  (HASHTEXTEXTENDED(COALESCE(s.work_history_id, ''), 0) & 9223372036854775807)::BIGINT
                                                      AS id,
  s.work_history_id::VARCHAR(64)                      AS ma_lich_su_cong_tac,
  s.social_worker_id::VARCHAR(64)                     AS ma_nhan_vien_ctxh,
  s.facility_code::VARCHAR(30)                        AS ma_co_so,
  s.facility_name::VARCHAR(255)                       AS ten_co_so,
  s.facility_type::VARCHAR(50)                        AS loai_co_so,
  s.position_code::VARCHAR(50)                        AS ma_vi_tri,
  s.position_name::VARCHAR(255)                       AS ten_vi_tri,
  s.contract_type_code::VARCHAR(50)                   AS ma_loai_hop_dong,
  s.contract_type_name::VARCHAR(255)                  AS ten_loai_hop_dong,
  s.job_description::TEXT                             AS mo_ta_cong_viec,
  s.start_date::DATE                                  AS ngay_bat_dau,
  s.end_date::DATE                                    AS ngay_ket_thuc,
  COALESCE(s.is_current, FALSE)::BOOLEAN              AS la_cong_tac_hien_tai,
  s.status::VARCHAR(50)                               AS trang_thai,
  'WORK_HISTORIES'::VARCHAR(20)                       AS nguon,
  s.updated_at::DATE                                  AS ngay_cap_nhat
FROM {stg_work_histories} s
WHERE s.work_history_id IS NOT NULL
  AND s.social_worker_id IS NOT NULL
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
      "BTXH social worker work history fact from WorkHistories first-level stream."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
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