from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "id": "bigint",
  "ma_ho_so_trung_tam": "text",
  "ma_nguoi_thu_huong": "text",
  "ma_co_so": "text",
  "ma_dinh_danh_nguon_co_so": "text",
  "ma_dinh_danh_y_te": "text",
  "nang_luc_lao_dong": "text",
  "ho_so_y_te": "text",
  "ma_loai_khuyet_tat": "text",
  "ma_nguyen_nhan_khuyet_tat": "text",
  "ma_muc_do_khuyet_tat": "text",
  "ma_kha_nang_tu_phuc_vu": "text",
  "tinh_trang_the_chat_tam_than": "text",
  "dac_diem_khuyet_tat": "text",
  "nguyen_nhan_khuyet_tat_khac": "text",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY center_profile_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_center_profile_medical_info}
  WHERE center_profile_id IS NOT NULL
)
SELECT
  (HASHTEXTEXTENDED(COALESCE(d.center_profile_id, ''), 0) & 9223372036854775807)::BIGINT
                                                            AS id,
  d.center_profile_id::VARCHAR(64)                          AS ma_ho_so_trung_tam,
  d.beneficiary_id::VARCHAR(64)                             AS ma_nguoi_thu_huong,
  d.facility_code::VARCHAR(30)                              AS ma_co_so,
  d.facility_id::VARCHAR(64)                                AS ma_dinh_danh_nguon_co_so,
  d.medical_person_id::VARCHAR(64)                          AS ma_dinh_danh_y_te,
  d.labor_capacity::TEXT                                    AS nang_luc_lao_dong,
  d.medical_record::TEXT                                    AS ho_so_y_te,
  d.disability_type_code::VARCHAR(50)                       AS ma_loai_khuyet_tat,
  d.disability_cause_code::VARCHAR(50)                      AS ma_nguyen_nhan_khuyet_tat,
  d.disability_level_code::VARCHAR(50)                      AS ma_muc_do_khuyet_tat,
  d.self_service_ability_code::VARCHAR(50)                  AS ma_kha_nang_tu_phuc_vu,
  d.physical_mental_status::TEXT                            AS tinh_trang_the_chat_tam_than,
  d.disability_characteristics::TEXT                        AS dac_diem_khuyet_tat,
  d.other_disability_cause::TEXT                            AS nguyen_nhan_khuyet_tat_khac,
  d.updated_at::DATE                                        AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_fact_ho_so_trung_tam_y_te",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_ho_so_trung_tam"),
    owner="data_team",
    cron="@daily",
    grain="ma_ho_so_trung_tam",
    tags=["fact", "btxh", "center_stay", "medical"],
    columns=MODEL_COLUMNS,
    description="BTXH center stay medical fact from center profile medical information.",
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    try:
        stg_center_profile_medical_info = context.resolve_table(
            "sqlmesh_work.btxh_stg_center_profile_medical_info"
        )
    except KeyError:
        stg_center_profile_medical_info = '"sqlmesh_work"."btxh_stg_center_profile_medical_info"'

    df = context.fetchdf(
        QUERY.format(
            stg_center_profile_medical_info=stg_center_profile_medical_info,
        )
    )
    if df.empty:
        yield from ()
        return
    yield df