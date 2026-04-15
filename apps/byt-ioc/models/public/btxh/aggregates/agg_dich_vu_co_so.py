from __future__ import annotations

import typing as t

import pandas as pd

from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
  "ngay_tinh_toan": "date",
  "ma_tinh": "text",
  "ma_loai_trung_tam": "text",
  "ten_loai_trung_tam": "text",
  "ma_hinh_thuc_co_so": "text",
  "ten_hinh_thuc_co_so": "text",
  "ma_dich_vu": "text",
  "ten_dich_vu": "text",
  "so_co_so_cung_cap_dich_vu": "bigint",
  "so_ho_so_dang_gan_dich_vu": "bigint",
  "so_nguoi_dang_su_dung_dich_vu": "bigint",
  "tong_cong_suat_ke_hoach": "bigint",
  "tong_nhan_su": "bigint",
  "tong_doi_tuong_hien_tai": "bigint",
}


QUERY = """
WITH latest_capacity AS (
  SELECT DISTINCT ON (f.ma_co_so)
    f.ma_co_so,
    f.cong_suat_ke_hoach,
    f.tong_nhan_su,
    f.tong_doi_tuong
  FROM {fact_nang_luc_co_so} f
  ORDER BY f.ma_co_so, f.ngay_cap_nhat DESC
),
service_usage AS (
  SELECT
    g.ma_co_so,
    g.ma_dich_vu,
    COALESCE(NULLIF(g.ten_dich_vu, ''), 'KHONG_XAC_DINH') AS ten_dich_vu,
    COUNT(DISTINCT g.ma_ho_so_trung_tam)                  AS so_ho_so_dang_gan_dich_vu,
    COUNT(DISTINCT g.ma_nguoi_thu_huong)                  AS so_nguoi_dang_su_dung_dich_vu
  FROM {fact_gan_dich_vu} g
  WHERE COALESCE(g.ho_so_da_xoa, FALSE) = FALSE
    AND COALESCE(g.ho_so_dang_hoat_dong, FALSE) = TRUE
  GROUP BY g.ma_co_so, g.ma_dich_vu, COALESCE(NULLIF(g.ten_dich_vu, ''), 'KHONG_XAC_DINH')
)
SELECT
  CURRENT_DATE::DATE                                      AS ngay_tinh_toan,
  COALESCE(cs.ma_tinh, '00')                              AS ma_tinh,
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH')        AS ma_loai_trung_tam,
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH')       AS ten_loai_trung_tam,
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH')       AS ma_hinh_thuc_co_so,
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH')      AS ten_hinh_thuc_co_so,
  su.ma_dich_vu::VARCHAR(50)                              AS ma_dich_vu,
  su.ten_dich_vu::VARCHAR(255)                            AS ten_dich_vu,
  COUNT(DISTINCT su.ma_co_so)::BIGINT                     AS so_co_so_cung_cap_dich_vu,
  COALESCE(SUM(su.so_ho_so_dang_gan_dich_vu), 0)::BIGINT  AS so_ho_so_dang_gan_dich_vu,
  COALESCE(SUM(su.so_nguoi_dang_su_dung_dich_vu), 0)::BIGINT
                                                           AS so_nguoi_dang_su_dung_dich_vu,
  COALESCE(SUM(lc.cong_suat_ke_hoach), 0)::BIGINT         AS tong_cong_suat_ke_hoach,
  COALESCE(SUM(lc.tong_nhan_su), 0)::BIGINT               AS tong_nhan_su,
  COALESCE(SUM(lc.tong_doi_tuong), 0)::BIGINT             AS tong_doi_tuong_hien_tai
FROM service_usage su
LEFT JOIN {dim_co_so} cs
  ON cs.ma_co_so = su.ma_co_so
LEFT JOIN latest_capacity lc
  ON lc.ma_co_so = su.ma_co_so
GROUP BY
  COALESCE(cs.ma_tinh, '00'),
  COALESCE(cs.ma_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_loai_trung_tam, 'KHONG_XAC_DINH'),
  COALESCE(cs.ma_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  COALESCE(cs.ten_hinh_thuc_co_so, 'KHONG_XAC_DINH'),
  su.ma_dich_vu,
  su.ten_dich_vu
"""


@model(
    name="public.btxh_agg_dich_vu_co_so",
    kind="full",
    owner="data_team",
    cron="@daily",
    grain=[
        "ngay_tinh_toan",
        "ma_tinh",
        "ma_loai_trung_tam",
        "ma_hinh_thuc_co_so",
        "ma_dich_vu",
    ],
    tags=["aggregate", "btxh", "service"],
    columns=MODEL_COLUMNS,
    description=(
        "BTXH facility-service aggregate combining active service assignments "
        "with the latest facility capacity snapshot."
    ),
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            fact_gan_dich_vu=context.resolve_table("public.btxh_fact_gan_dich_vu"),
            fact_nang_luc_co_so=context.resolve_table("public.btxh_fact_nang_luc_co_so"),
            dim_co_so=context.resolve_table("public.btxh_dim_co_so"),
        )
    )
    if df.empty:
        yield from ()
        return
    yield df