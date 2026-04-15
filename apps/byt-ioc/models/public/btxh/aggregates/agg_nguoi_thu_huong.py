from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "ngay_tinh_toan": "date",
  "ma_tinh": "text",
  "ma_co_so": "text",
  "ma_loai_trung_tam": "text",
  "ten_loai_trung_tam": "text",
  "ma_hinh_thuc_co_so": "text",
  "ten_hinh_thuc_co_so": "text",
  "ma_nhom_doi_tuong": "text",
  "gioi_tinh": "text",
  "nhom_tuoi": "text",
  "nhom_tuoi_chi_tiet": "text",
  "trang_thai_nguoi_thu_huong": "text",
  "trang_thai_ho_so": "text",
  "loai_luu_tru": "text",
  "so_nguoi_thu_huong": "bigint",
  "so_nguoi_co_ho_so_trung_tam": "bigint",
  "so_nguoi_co_ho_so_hoat_dong": "bigint",
}


QUERY = """
WITH current_profile AS (
  SELECT DISTINCT
    hs.ma_nguoi_thu_huong,
    hs.ma_co_so,
    hs.trang_thai_ho_so,
    hs.loai_luu_tru
  FROM {fact_ho_so_trung_tam} hs
  WHERE COALESCE(hs.ho_so_da_xoa, FALSE) = FALSE
    AND COALESCE(hs.ho_so_dang_hoat_dong, FALSE) = TRUE
),
current_group AS (
  SELECT DISTINCT
    ng.ma_nguoi_thu_huong,
    ng.ma_co_so,
    ng.ma_nhom_doi_tuong
  FROM {fact_ho_so_trung_tam_nhom_doi_tuong} ng
  JOIN {fact_ho_so_trung_tam} hs
    ON hs.ma_ho_so_trung_tam = ng.ma_ho_so_trung_tam
  WHERE COALESCE(hs.ho_so_da_xoa, FALSE) = FALSE
    AND COALESCE(hs.ho_so_dang_hoat_dong, FALSE) = TRUE
),
base AS (
  SELECT
    CURRENT_DATE::DATE                                            AS ngay_tinh_toan,
    COALESCE(cs.ma_tinh, d.ma_tinh, '00')                         AS ma_tinh,
    COALESCE(d.ma_co_so_hien_tai, cp.ma_co_so, 'KHONG_XAC_DINH')  AS ma_co_so,
    COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH')              AS ma_loai_trung_tam,
    COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH')             AS ten_loai_trung_tam,
    COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH')             AS ma_hinh_thuc_co_so,
    COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH')            AS ten_hinh_thuc_co_so,
    COALESCE(cg.ma_nhom_doi_tuong, 'KHONG_XAC_DINH')              AS ma_nhom_doi_tuong,
    COALESCE(d.gioi_tinh, 'KHONG_XAC_DINH')                       AS gioi_tinh,
    CASE
      WHEN d.nam_sinh IS NULL THEN 'KHONG_XAC_DINH'
      WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh < 18 THEN '0-17'
      WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh < 60 THEN '18-59'
      ELSE '60+'
    END                                                           AS nhom_tuoi,
    CASE
      WHEN d.nam_sinh IS NULL THEN 'KHONG_XAC_DINH'
      WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh BETWEEN 0 AND 5 THEN '0-5'
      WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh BETWEEN 6 AND 14 THEN '6-14'
      WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh BETWEEN 15 AND 17 THEN '15-17'
      WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh BETWEEN 18 AND 59 THEN '18-59'
      ELSE '60+'
    END                                                           AS nhom_tuoi_chi_tiet,
    COALESCE(d.trang_thai_nguoi_thu_huong, 'KHONG_XAC_DINH')      AS trang_thai_nguoi_thu_huong,
    COALESCE(cp.trang_thai_ho_so, d.trang_thai_ho_so, 'KHONG_XAC_DINH')
                                                                  AS trang_thai_ho_so,
    COALESCE(cp.loai_luu_tru, 'KHONG_XAC_DINH')                   AS loai_luu_tru,
    d.ma_nguoi_thu_huong,
    d.co_ho_so_trung_tam,
    d.so_ho_so_trung_tam_hoat_dong
  FROM {dim_nguoi_thu_huong} d
  LEFT JOIN current_profile cp
    ON cp.ma_nguoi_thu_huong = d.ma_nguoi_thu_huong
   AND cp.ma_co_so = d.ma_co_so_hien_tai
  LEFT JOIN current_group cg
    ON cg.ma_nguoi_thu_huong = d.ma_nguoi_thu_huong
   AND cg.ma_co_so = COALESCE(d.ma_co_so_hien_tai, cp.ma_co_so)
  LEFT JOIN {dim_co_so} cs
    ON cs.ma_co_so = COALESCE(d.ma_co_so_hien_tai, cp.ma_co_so)
)
SELECT
  ngay_tinh_toan,
  ma_tinh,
  ma_co_so,
  ma_loai_trung_tam,
  ten_loai_trung_tam,
  ma_hinh_thuc_co_so,
  ten_hinh_thuc_co_so,
  ma_nhom_doi_tuong,
  gioi_tinh,
  nhom_tuoi,
  nhom_tuoi_chi_tiet,
  trang_thai_nguoi_thu_huong,
  trang_thai_ho_so,
  loai_luu_tru,
  COUNT(DISTINCT ma_nguoi_thu_huong)::BIGINT                                          AS so_nguoi_thu_huong,
  COUNT(DISTINCT CASE WHEN COALESCE(co_ho_so_trung_tam, FALSE) THEN ma_nguoi_thu_huong END)::BIGINT
                                                                                        AS so_nguoi_co_ho_so_trung_tam,
  COUNT(DISTINCT CASE WHEN COALESCE(so_ho_so_trung_tam_hoat_dong, 0) > 0 THEN ma_nguoi_thu_huong END)::BIGINT
                                                                                        AS so_nguoi_co_ho_so_hoat_dong
FROM base
GROUP BY
  ngay_tinh_toan,
  ma_tinh,
  ma_co_so,
  ma_loai_trung_tam,
  ten_loai_trung_tam,
  ma_hinh_thuc_co_so,
  ten_hinh_thuc_co_so,
  ma_nhom_doi_tuong,
  gioi_tinh,
  nhom_tuoi,
  nhom_tuoi_chi_tiet,
  trang_thai_nguoi_thu_huong,
  trang_thai_ho_so,
  loai_luu_tru
"""


@model(
    name="public.btxh_agg_nguoi_thu_huong",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain=[
        "ngay_tinh_toan",
        "ma_tinh",
        "ma_co_so",
        "ma_nhom_doi_tuong",
        "gioi_tinh",
        "nhom_tuoi",
        "nhom_tuoi_chi_tiet",
        "trang_thai_nguoi_thu_huong",
        "trang_thai_ho_so",
        "loai_luu_tru",
    ],
    tags=["aggregate", "btxh", "beneficiary"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH beneficiary aggregate by province, facility, beneficiary group, "
        "gender, age band, and current profile status."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            dim_nguoi_thu_huong=context.resolve_table("public.btxh_dim_nguoi_thu_huong"),
            dim_co_so=context.resolve_table("public.btxh_dim_co_so"),
            fact_ho_so_trung_tam=context.resolve_table("public.btxh_fact_ho_so_trung_tam"),
            fact_ho_so_trung_tam_nhom_doi_tuong=context.resolve_table(
                "public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong"
            ),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df