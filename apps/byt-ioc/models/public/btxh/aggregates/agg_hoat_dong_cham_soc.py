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
  "trang_thai_ke_hoach_cham_soc": "text",
  "ma_muc_tieu": "text",
  "ma_linh_vuc_danh_gia": "text",
  "muc_do_uu_tien": "text",
  "gioi_tinh_nguoi_thu_huong": "text",
  "nhom_tuoi_nguoi_thu_huong": "text",
  "so_hoat_dong_cham_soc": "bigint",
  "so_ke_hoach_cham_soc": "bigint",
  "so_nguoi_thu_huong": "bigint",
  "tong_so_don_vi_thuc_hien": "bigint",
}


QUERY = """
SELECT
  CURRENT_DATE::DATE                                           AS ngay_tinh_toan,
  COALESCE(cs.ma_tinh, d.ma_tinh, '00')                        AS ma_tinh,
  COALESCE(h.ma_co_so, d.ma_co_so_hien_tai, 'KHONG_XAC_DINH')  AS ma_co_so,
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH')             AS ma_loai_trung_tam,
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH')            AS ten_loai_trung_tam,
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH')            AS ma_hinh_thuc_co_so,
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH')           AS ten_hinh_thuc_co_so,
  COALESCE(h.trang_thai_ke_hoach_cham_soc, 'KHONG_XAC_DINH')   AS trang_thai_ke_hoach_cham_soc,
  COALESCE(h.ma_muc_tieu, 'KHONG_XAC_DINH')                    AS ma_muc_tieu,
  COALESCE(h.ma_linh_vuc_danh_gia, 'KHONG_XAC_DINH')           AS ma_linh_vuc_danh_gia,
  COALESCE(h.muc_do_uu_tien, 'KHONG_XAC_DINH')                 AS muc_do_uu_tien,
  COALESCE(d.gioi_tinh, 'KHONG_XAC_DINH')                      AS gioi_tinh_nguoi_thu_huong,
  CASE
    WHEN d.nam_sinh IS NULL THEN 'KHONG_XAC_DINH'
    WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh < 18 THEN '0-17'
    WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh < 60 THEN '18-59'
    ELSE '60+'
  END                                                          AS nhom_tuoi_nguoi_thu_huong,
  COUNT(DISTINCT h.ma_hoat_dong_cham_soc)::BIGINT              AS so_hoat_dong_cham_soc,
  COUNT(DISTINCT h.ma_ke_hoach_cham_soc)::BIGINT               AS so_ke_hoach_cham_soc,
  COUNT(DISTINCT h.ma_nguoi_thu_huong)::BIGINT                 AS so_nguoi_thu_huong,
  COALESCE(SUM(h.so_don_vi_thuc_hien), 0)::BIGINT              AS tong_so_don_vi_thuc_hien
FROM {fact_hoat_dong_cham_soc} h
LEFT JOIN {dim_nguoi_thu_huong} d
  ON d.ma_nguoi_thu_huong = h.ma_nguoi_thu_huong
LEFT JOIN {dim_co_so} cs
  ON cs.ma_co_so = COALESCE(h.ma_co_so, d.ma_co_so_hien_tai)
GROUP BY
  COALESCE(cs.ma_tinh, d.ma_tinh, '00'),
  COALESCE(h.ma_co_so, d.ma_co_so_hien_tai, 'KHONG_XAC_DINH'),
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(h.trang_thai_ke_hoach_cham_soc, 'KHONG_XAC_DINH'),
  COALESCE(h.ma_muc_tieu, 'KHONG_XAC_DINH'),
  COALESCE(h.ma_linh_vuc_danh_gia, 'KHONG_XAC_DINH'),
  COALESCE(h.muc_do_uu_tien, 'KHONG_XAC_DINH'),
  COALESCE(d.gioi_tinh, 'KHONG_XAC_DINH'),
  CASE
    WHEN d.nam_sinh IS NULL THEN 'KHONG_XAC_DINH'
    WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh < 18 THEN '0-17'
    WHEN EXTRACT(YEAR FROM CURRENT_DATE) - d.nam_sinh < 60 THEN '18-59'
    ELSE '60+'
  END
"""


@model(
    name="public.btxh_agg_hoat_dong_cham_soc",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain=[
        "ngay_tinh_toan",
        "ma_tinh",
        "ma_co_so",
        "trang_thai_ke_hoach_cham_soc",
        "ma_muc_tieu",
        "ma_linh_vuc_danh_gia",
        "muc_do_uu_tien",
        "gioi_tinh_nguoi_thu_huong",
        "nhom_tuoi_nguoi_thu_huong",
    ],
    tags=["aggregate", "btxh", "care_activity"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH care-activity aggregate by province, facility, plan status, goal, "
        "assessment field, beneficiary gender, and age band."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            fact_hoat_dong_cham_soc=context.resolve_table("public.btxh_fact_hoat_dong_cham_soc"),
            dim_nguoi_thu_huong=context.resolve_table("public.btxh_dim_nguoi_thu_huong"),
            dim_co_so=context.resolve_table("public.btxh_dim_co_so"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df