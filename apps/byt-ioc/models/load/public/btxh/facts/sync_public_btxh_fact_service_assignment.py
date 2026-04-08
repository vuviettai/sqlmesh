from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_fact_gan_dich_vu",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_btxh_fact_gan_dich_vu",
        "sqlmesh_work.sync_public_btxh_dim_nguoi_thu_huong",
        "sqlmesh_work.sync_public_btxh_dim_co_so",
        "sqlmesh_work.sync_public_btxh_dim_dich_vu",
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_fact_gan_dich_vu")
    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} s
            JOIN public.btxh_dim_nguoi_thu_huong b ON b.ma_nguoi_thu_huong = s.ma_nguoi_thu_huong
            JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
            JOIN public.btxh_dim_dich_vu d ON d.ma_dich_vu = s.ma_dich_vu
            """
        ).iloc[0]["cnt"]
    )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_fact_gan_dich_vu (
            ma_ho_so_trung_tam,
            ma_nguoi_thu_huong,
            ma_co_so,
            ma_dich_vu,
            ten_dich_vu,
            ngay_tiep_nhan,
            ngay_quyet_dinh_tiep_nhan,
            trang_thai_ho_so,
            loai_luu_tru,
            ho_so_dang_hoat_dong,
            ho_so_da_xoa,
            ngay_cap_nhat
        )
        SELECT
            s.ma_ho_so_trung_tam,
            s.ma_nguoi_thu_huong,
            s.ma_co_so,
            s.ma_dich_vu,
            s.ten_dich_vu,
            s.ngay_tiep_nhan,
            s.ngay_quyet_dinh_tiep_nhan,
            s.trang_thai_ho_so,
            s.loai_luu_tru,
            s.ho_so_dang_hoat_dong,
            s.ho_so_da_xoa,
            s.ngay_cap_nhat
        FROM {source_table} s
        JOIN public.btxh_dim_nguoi_thu_huong b ON b.ma_nguoi_thu_huong = s.ma_nguoi_thu_huong
        JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
        JOIN public.btxh_dim_dich_vu d ON d.ma_dich_vu = s.ma_dich_vu
        ON CONFLICT (ma_ho_so_trung_tam, ma_dich_vu) DO UPDATE SET
            ma_nguoi_thu_huong = EXCLUDED.ma_nguoi_thu_huong,
            ma_co_so = EXCLUDED.ma_co_so,
            ten_dich_vu = EXCLUDED.ten_dich_vu,
            ngay_tiep_nhan = EXCLUDED.ngay_tiep_nhan,
            ngay_quyet_dinh_tiep_nhan = EXCLUDED.ngay_quyet_dinh_tiep_nhan,
            trang_thai_ho_so = EXCLUDED.trang_thai_ho_so,
            loai_luu_tru = EXCLUDED.loai_luu_tru,
            ho_so_dang_hoat_dong = EXCLUDED.ho_so_dang_hoat_dong,
            ho_so_da_xoa = EXCLUDED.ho_so_da_xoa,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    return pd.DataFrame([
        {"target_table": "public.btxh_fact_gan_dich_vu", "rows_loaded": matched_rows, "loaded_at": execution_time}
    ])