from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_fact_nang_luc_co_so",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_btxh_fact_nang_luc_co_so",
        "sqlmesh_work.sync_public_btxh_dim_co_so",
    ],
    columns={"target_table": "text", "rows_loaded": "bigint", "loaded_at": "timestamp"},
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    del start, end, kwargs

    source_table = context.resolve_table("sqlmesh_work.src_btxh_fact_nang_luc_co_so")
    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} s
            JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
            """
        ).iloc[0]["cnt"]
    )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_fact_nang_luc_co_so (
            ma_co_so,
            ma_dinh_danh_nguon_co_so,
            ma_loai_trung_tam,
            ma_hinh_thuc_co_so,
            cong_suat_ke_hoach,
            tong_nhan_su,
            tong_doi_tuong,
            tong_dien_tich,
            dien_tich_binh_quan_mot_doi_tuong,
            dien_tich_nha_o_binh_quan_mot_doi_tuong,
            dang_hoat_dong,
            ngay_cap_nhat
        )
        SELECT
            s.ma_co_so,
            s.ma_dinh_danh_nguon_co_so,
            s.ma_loai_trung_tam,
            s.ma_hinh_thuc_co_so,
            s.cong_suat_ke_hoach,
            s.tong_nhan_su,
            s.tong_doi_tuong,
            s.tong_dien_tich,
            s.dien_tich_binh_quan_mot_doi_tuong,
            s.dien_tich_nha_o_binh_quan_mot_doi_tuong,
            s.dang_hoat_dong,
            s.ngay_cap_nhat
        FROM {source_table} s
        JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
        ON CONFLICT (ma_co_so, ngay_cap_nhat) DO UPDATE SET
            ma_dinh_danh_nguon_co_so = EXCLUDED.ma_dinh_danh_nguon_co_so,
            ma_loai_trung_tam = EXCLUDED.ma_loai_trung_tam,
            ma_hinh_thuc_co_so = EXCLUDED.ma_hinh_thuc_co_so,
            cong_suat_ke_hoach = EXCLUDED.cong_suat_ke_hoach,
            tong_nhan_su = EXCLUDED.tong_nhan_su,
            tong_doi_tuong = EXCLUDED.tong_doi_tuong,
            tong_dien_tich = EXCLUDED.tong_dien_tich,
            dien_tich_binh_quan_mot_doi_tuong = EXCLUDED.dien_tich_binh_quan_mot_doi_tuong,
            dien_tich_nha_o_binh_quan_mot_doi_tuong = EXCLUDED.dien_tich_nha_o_binh_quan_mot_doi_tuong,
            dang_hoat_dong = EXCLUDED.dang_hoat_dong
        """
    )

    return pd.DataFrame([
        {
            "target_table": "public.btxh_fact_nang_luc_co_so",
            "rows_loaded": matched_rows,
            "loaded_at": execution_time,
        }
    ])