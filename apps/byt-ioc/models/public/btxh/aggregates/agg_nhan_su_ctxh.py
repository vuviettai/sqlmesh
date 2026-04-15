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
  "ma_vi_tri": "text",
  "ten_vi_tri": "text",
  "ma_loai_hop_dong": "text",
  "ten_loai_hop_dong": "text",
  "ma_trinh_do_hoc_van": "text",
  "ten_trinh_do_hoc_van": "text",
  "gioi_tinh": "text",
  "nhom_tuoi": "text",
  "co_cong_tac_hien_tai": "boolean",
  "so_nhan_vien": "bigint",
}


QUERY = """
WITH current_assignment AS (
  SELECT DISTINCT ON (f.ma_nhan_vien_ctxh)
    f.ma_nhan_vien_ctxh,
    f.ma_co_so,
    f.ma_vi_tri,
    f.ten_vi_tri,
    f.ma_loai_hop_dong,
    f.ten_loai_hop_dong
  FROM {fact_lich_su_cong_tac_xh} f
  WHERE COALESCE(f.la_cong_tac_hien_tai, FALSE) = TRUE
  ORDER BY f.ma_nhan_vien_ctxh, f.ngay_cap_nhat DESC
)
SELECT
  CURRENT_DATE::DATE                                           AS ngay_tinh_toan,
  COALESCE(cs.ma_tinh, nv.ma_tinh, '00')                       AS ma_tinh,
  COALESCE(ca.ma_co_so, nv.ma_co_so_hien_tai, 'KHONG_XAC_DINH') AS ma_co_so,
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH')             AS ma_loai_trung_tam,
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH')            AS ten_loai_trung_tam,
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH')            AS ma_hinh_thuc_co_so,
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH')           AS ten_hinh_thuc_co_so,
  COALESCE(ca.ma_vi_tri, nv.ma_vi_tri_hien_tai, 'KHONG_XAC_DINH')
                                                                 AS ma_vi_tri,
  COALESCE(ca.ten_vi_tri, nv.ten_vi_tri_hien_tai, 'KHONG_XAC_DINH')
                                                                 AS ten_vi_tri,
  COALESCE(ca.ma_loai_hop_dong, nv.ma_loai_hop_dong_hien_tai, 'KHONG_XAC_DINH')
                                                                 AS ma_loai_hop_dong,
  COALESCE(ca.ten_loai_hop_dong, nv.ten_loai_hop_dong_hien_tai, 'KHONG_XAC_DINH')
                                                                 AS ten_loai_hop_dong,
  COALESCE(nv.ma_trinh_do_hoc_van, 'KHONG_XAC_DINH')           AS ma_trinh_do_hoc_van,
  COALESCE(nv.ten_trinh_do_hoc_van, 'KHONG_XAC_DINH')          AS ten_trinh_do_hoc_van,
  COALESCE(nv.gioi_tinh, 'KHONG_XAC_DINH')                     AS gioi_tinh,
  CASE
    WHEN nv.ngay_sinh IS NULL THEN 'KHONG_XAC_DINH'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, nv.ngay_sinh)) < 30 THEN '<30'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, nv.ngay_sinh)) < 45 THEN '30-44'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, nv.ngay_sinh)) < 60 THEN '45-59'
    ELSE '60+'
  END                                                          AS nhom_tuoi,
  (ca.ma_nhan_vien_ctxh IS NOT NULL)                           AS co_cong_tac_hien_tai,
  COUNT(DISTINCT nv.ma_nhan_vien_ctxh)::BIGINT                 AS so_nhan_vien
FROM {dim_nhan_vien_ctxh} nv
LEFT JOIN current_assignment ca
  ON ca.ma_nhan_vien_ctxh = nv.ma_nhan_vien_ctxh
LEFT JOIN {dim_co_so} cs
  ON cs.ma_co_so = COALESCE(ca.ma_co_so, nv.ma_co_so_hien_tai)
GROUP BY
  COALESCE(cs.ma_tinh, nv.ma_tinh, '00'),
  COALESCE(ca.ma_co_so, nv.ma_co_so_hien_tai, 'KHONG_XAC_DINH'),
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(ca.ma_vi_tri, nv.ma_vi_tri_hien_tai, 'KHONG_XAC_DINH'),
  COALESCE(ca.ten_vi_tri, nv.ten_vi_tri_hien_tai, 'KHONG_XAC_DINH'),
  COALESCE(ca.ma_loai_hop_dong, nv.ma_loai_hop_dong_hien_tai, 'KHONG_XAC_DINH'),
  COALESCE(ca.ten_loai_hop_dong, nv.ten_loai_hop_dong_hien_tai, 'KHONG_XAC_DINH'),
  COALESCE(nv.ma_trinh_do_hoc_van, 'KHONG_XAC_DINH'),
  COALESCE(nv.ten_trinh_do_hoc_van, 'KHONG_XAC_DINH'),
  COALESCE(nv.gioi_tinh, 'KHONG_XAC_DINH'),
  CASE
    WHEN nv.ngay_sinh IS NULL THEN 'KHONG_XAC_DINH'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, nv.ngay_sinh)) < 30 THEN '<30'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, nv.ngay_sinh)) < 45 THEN '30-44'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, nv.ngay_sinh)) < 60 THEN '45-59'
    ELSE '60+'
  END,
  (ca.ma_nhan_vien_ctxh IS NOT NULL)
"""


@model(
    name="public.btxh_agg_nhan_su_ctxh",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain=[
        "ngay_tinh_toan",
        "ma_tinh",
        "ma_co_so",
        "ma_vi_tri",
        "ma_loai_hop_dong",
        "ma_trinh_do_hoc_van",
        "gioi_tinh",
        "nhom_tuoi",
        "co_cong_tac_hien_tai",
    ],
    tags=["aggregate", "btxh", "social_worker"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH social-worker aggregate by province, facility, role, contract, "
        "education, gender, and age band."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            dim_nhan_vien_ctxh=context.resolve_table("public.btxh_dim_nhan_vien_ctxh"),
            fact_lich_su_cong_tac_xh=context.resolve_table("public.btxh_fact_lich_su_cong_tac_xh"),
            dim_co_so=context.resolve_table("public.btxh_dim_co_so"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df