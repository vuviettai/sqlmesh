from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "ngay_cap_nhat": "date",
  "ma_tinh": "text",
  "ma_loai_trung_tam": "text",
  "ten_loai_trung_tam": "text",
  "ma_hinh_thuc_co_so": "text",
  "ten_hinh_thuc_co_so": "text",
  "dang_hoat_dong": "boolean",
  "so_co_so": "bigint",
  "tong_cong_suat_ke_hoach": "bigint",
  "tong_nhan_su": "bigint",
  "tong_doi_tuong": "bigint",
  "tong_dien_tich": "decimal(18, 2)",
  "dien_tich_binh_quan_mot_doi_tuong": "decimal(18, 2)",
  "dien_tich_nha_o_binh_quan_mot_doi_tuong": "decimal(18, 2)",
  "ty_le_lap_day": "decimal(7, 2)",
}


QUERY = """
SELECT
  f.ngay_cap_nhat::DATE                                           AS ngay_cap_nhat,
  COALESCE(cs.ma_tinh, '00')                                      AS ma_tinh,
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH')                AS ma_loai_trung_tam,
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH')               AS ten_loai_trung_tam,
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH')               AS ma_hinh_thuc_co_so,
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH')              AS ten_hinh_thuc_co_so,
  COALESCE(f.dang_hoat_dong, FALSE)                               AS dang_hoat_dong,
  COUNT(DISTINCT f.ma_co_so)::BIGINT                              AS so_co_so,
  COALESCE(SUM(f.cong_suat_ke_hoach), 0)::BIGINT                  AS tong_cong_suat_ke_hoach,
  COALESCE(SUM(f.tong_nhan_su), 0)::BIGINT                        AS tong_nhan_su,
  COALESCE(SUM(f.tong_doi_tuong), 0)::BIGINT                      AS tong_doi_tuong,
  COALESCE(SUM(f.tong_dien_tich), 0)::DECIMAL(18, 2)              AS tong_dien_tich,
  ROUND(
    COALESCE(SUM(f.tong_dien_tich), 0)::NUMERIC
    / NULLIF(COALESCE(SUM(f.tong_doi_tuong), 0), 0),
    2
  )::DECIMAL(18, 2)                                               AS dien_tich_binh_quan_mot_doi_tuong,
  ROUND(AVG(f.dien_tich_nha_o_binh_quan_mot_doi_tuong)::NUMERIC, 2)::DECIMAL(18, 2)
                                                                   AS dien_tich_nha_o_binh_quan_mot_doi_tuong,
  ROUND(
    COALESCE(SUM(f.tong_doi_tuong), 0)::NUMERIC
    / NULLIF(COALESCE(SUM(f.cong_suat_ke_hoach), 0), 0) * 100,
    2
  )::DECIMAL(7, 2)                                                AS ty_le_lap_day
FROM {fact_nang_luc_co_so} f
LEFT JOIN {dim_co_so} cs
  ON cs.ma_co_so = f.ma_co_so
GROUP BY
  f.ngay_cap_nhat,
  COALESCE(cs.ma_tinh, '00'),
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(f.dang_hoat_dong, FALSE)
"""


@model(
    name="public.btxh_agg_nang_luc_co_so_daily",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain=[
        "ngay_cap_nhat",
        "ma_tinh",
        "ma_loai_trung_tam",
        "ma_hinh_thuc_co_so",
        "dang_hoat_dong",
    ],
    tags=["aggregate", "btxh", "facility_capacity"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH daily facility capacity aggregate by province, center type, and "
        "facility form."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            fact_nang_luc_co_so=context.resolve_table("public.btxh_fact_nang_luc_co_so"),
            dim_co_so=context.resolve_table("public.btxh_dim_co_so"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df