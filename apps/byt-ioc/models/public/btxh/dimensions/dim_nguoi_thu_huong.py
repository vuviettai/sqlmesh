from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName


MODEL_COLUMNS = {
  "ma_nguoi_thu_huong": "text",
  "ho_va_ten": "text",
  "gioi_tinh": "text",
  "nam_sinh": "int",
  "thang_sinh": "int",
  "ngay_sinh": "int",
  "ma_tinh": "text",
  "dia_chi": "text",
  "dan_toc": "text",
  "quoc_tich": "text",
  "noi_sinh": "text",
  "so_giay_to": "text",
  "ma_loai_giay_to": "text",
  "ma_co_so_hien_tai": "text",
  "ten_co_so_hien_tai": "text",
  "trang_thai_nguoi_thu_huong": "text",
  "trang_thai_ho_so": "text",
  "co_ho_so_trung_tam": "boolean",
  "so_ho_so_trung_tam": "int",
  "so_ho_so_trung_tam_hoat_dong": "int",
  "ngay_cap_nhat": "date",
}


QUERY = """
WITH deduped AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY beneficiary_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM {stg_beneficiaries}
  WHERE beneficiary_id IS NOT NULL
)
SELECT
  d.beneficiary_id::VARCHAR(64)                                 AS ma_nguoi_thu_huong,
  d.ho_va_ten::VARCHAR(255)                                     AS ho_va_ten,
  d.gioi_tinh::VARCHAR(50)                                      AS gioi_tinh,
  EXTRACT(YEAR  FROM d.ngay_sinh::DATE)::INT                    AS nam_sinh,
  EXTRACT(MONTH FROM d.ngay_sinh::DATE)::INT                    AS thang_sinh,
  EXTRACT(DAY   FROM d.ngay_sinh::DATE)::INT                    AS ngay_sinh,
  COALESCE(NULLIF(d.ma_tinh_moi, ''), NULLIF(d.ma_tinh_hien_tai, ''), '00')::VARCHAR(10)
                                                                AS ma_tinh,
  COALESCE(NULLIF(d.dia_chi_moi, ''), d.dia_chi_hien_tai)::TEXT AS dia_chi,
  d.dan_toc::VARCHAR(50)                                        AS dan_toc,
  d.quoc_tich::VARCHAR(50)                                      AS quoc_tich,
  d.noi_sinh::VARCHAR(255)                                      AS noi_sinh,
  d.so_giay_to::VARCHAR(50)                                     AS so_giay_to,
  d.ma_loai_giay_to::VARCHAR(20)                                AS ma_loai_giay_to,
  d.ma_co_so_hien_tai::VARCHAR(30)                              AS ma_co_so_hien_tai,
  d.ten_co_so_hien_tai::VARCHAR(255)                            AS ten_co_so_hien_tai,
  CASE
    WHEN d.is_active IS TRUE THEN 'DANG_HOAT_DONG'
    ELSE 'NGUNG_HOAT_DONG'
  END::VARCHAR(50)                                              AS trang_thai_nguoi_thu_huong,
  COALESCE(d.ma_trang_thai_ho_so, 'KHONG_CO_HO_SO')::VARCHAR(50)
                                                                AS trang_thai_ho_so,
  COALESCE(d.co_ho_so_trung_tam, FALSE)::BOOLEAN                AS co_ho_so_trung_tam,
  COALESCE(d.so_ho_so_trung_tam, 0)::INT                        AS so_ho_so_trung_tam,
  COALESCE(d.so_ho_so_trung_tam_hoat_dong, 0)::INT              AS so_ho_so_trung_tam_hoat_dong,
  d.updated_at::DATE                                            AS ngay_cap_nhat
FROM deduped d
WHERE d.rn = 1
"""


@model(
    name="public.btxh_dim_nguoi_thu_huong",
    kind=dict(name=ModelKindName.INCREMENTAL_BY_UNIQUE_KEY, unique_key="ma_nguoi_thu_huong"),
    owner="data_team",
    cron="@daily",
    grain="ma_nguoi_thu_huong",
    tags=["dimension", "btxh", "beneficiary"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH beneficiary dimension - latest demographics and current support "
        "status per beneficiary."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_beneficiaries=context.resolve_table("sqlmesh_work.btxh_stg_beneficiaries")
        )
    )
    if df.empty:
        yield from ()
        return
    yield df