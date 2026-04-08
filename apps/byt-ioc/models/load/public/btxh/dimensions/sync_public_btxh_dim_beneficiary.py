from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_dim_nguoi_thu_huong",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=["sqlmesh_work.src_btxh_dim_nguoi_thu_huong"],
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_dim_nguoi_thu_huong")
    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_dim_nguoi_thu_huong (
            ma_nguoi_thu_huong,
            ho_va_ten,
            gioi_tinh,
            ngay_sinh,
            nhom_tuoi,
            ma_tinh,
            dia_chi,
            dan_toc,
            quoc_tich,
            noi_sinh,
            so_giay_to,
            ma_loai_giay_to,
            ma_co_so_hien_tai,
            ten_co_so_hien_tai,
            trang_thai_nguoi_thu_huong,
            trang_thai_ho_so,
            co_ho_so_trung_tam,
            so_ho_so_trung_tam,
            so_ho_so_trung_tam_hoat_dong,
            ngay_cap_nhat
        )
        SELECT
            ma_nguoi_thu_huong,
            ho_va_ten,
            gioi_tinh,
            ngay_sinh,
            nhom_tuoi,
            ma_tinh,
            dia_chi,
            dan_toc,
            quoc_tich,
            noi_sinh,
            so_giay_to,
            ma_loai_giay_to,
            ma_co_so_hien_tai,
            ten_co_so_hien_tai,
            trang_thai_nguoi_thu_huong,
            trang_thai_ho_so,
            co_ho_so_trung_tam,
            so_ho_so_trung_tam,
            so_ho_so_trung_tam_hoat_dong,
            ngay_cap_nhat
        FROM {source_table}
        ON CONFLICT (ma_nguoi_thu_huong) DO UPDATE SET
            ho_va_ten = EXCLUDED.ho_va_ten,
            gioi_tinh = EXCLUDED.gioi_tinh,
            ngay_sinh = EXCLUDED.ngay_sinh,
            nhom_tuoi = EXCLUDED.nhom_tuoi,
            ma_tinh = EXCLUDED.ma_tinh,
            dia_chi = EXCLUDED.dia_chi,
            dan_toc = EXCLUDED.dan_toc,
            quoc_tich = EXCLUDED.quoc_tich,
            noi_sinh = EXCLUDED.noi_sinh,
            so_giay_to = EXCLUDED.so_giay_to,
            ma_loai_giay_to = EXCLUDED.ma_loai_giay_to,
            ma_co_so_hien_tai = EXCLUDED.ma_co_so_hien_tai,
            ten_co_so_hien_tai = EXCLUDED.ten_co_so_hien_tai,
            trang_thai_nguoi_thu_huong = EXCLUDED.trang_thai_nguoi_thu_huong,
            trang_thai_ho_so = EXCLUDED.trang_thai_ho_so,
            co_ho_so_trung_tam = EXCLUDED.co_ho_so_trung_tam,
            so_ho_so_trung_tam = EXCLUDED.so_ho_so_trung_tam,
            so_ho_so_trung_tam_hoat_dong = EXCLUDED.so_ho_so_trung_tam_hoat_dong,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    rows_loaded = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    return pd.DataFrame([
        {"target_table": "public.btxh_dim_nguoi_thu_huong", "rows_loaded": rows_loaded, "loaded_at": execution_time}
    ])