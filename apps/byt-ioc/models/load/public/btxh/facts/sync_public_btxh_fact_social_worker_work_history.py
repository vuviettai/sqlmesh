from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_fact_lich_su_cong_tac_nhan_vien_ctxh",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_btxh_fact_lich_su_cong_tac_nhan_vien_ctxh",
        "sqlmesh_work.sync_public_btxh_dim_nhan_vien_ctxh",
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_fact_lich_su_cong_tac_nhan_vien_ctxh")
    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} s
            JOIN public.btxh_dim_nhan_vien_ctxh w ON w.ma_nhan_vien_ctxh = s.ma_nhan_vien_ctxh
            LEFT JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
            """
        ).iloc[0]["cnt"]
    )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_fact_lich_su_cong_tac_nhan_vien_ctxh (
            ma_lich_su_cong_tac,
            ma_nhan_vien_ctxh,
            ma_co_so,
            ten_co_so,
            loai_co_so,
            ngay_bat_dau,
            ngay_ket_thuc,
            la_cong_tac_hien_tai,
            trang_thai,
            ma_vi_tri,
            ten_vi_tri,
            ma_loai_hop_dong,
            ten_loai_hop_dong,
            mo_ta_cong_viec,
            ngay_cap_nhat
        )
        SELECT
            s.ma_lich_su_cong_tac,
            s.ma_nhan_vien_ctxh,
            s.ma_co_so,
            s.ten_co_so,
            s.loai_co_so,
            s.ngay_bat_dau,
            s.ngay_ket_thuc,
            s.la_cong_tac_hien_tai,
            s.trang_thai,
            s.ma_vi_tri,
            s.ten_vi_tri,
            s.ma_loai_hop_dong,
            s.ten_loai_hop_dong,
            s.mo_ta_cong_viec,
            s.ngay_cap_nhat
        FROM {source_table} s
        JOIN public.btxh_dim_nhan_vien_ctxh w ON w.ma_nhan_vien_ctxh = s.ma_nhan_vien_ctxh
        LEFT JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
        ON CONFLICT (ma_lich_su_cong_tac) DO UPDATE SET
            ma_nhan_vien_ctxh = EXCLUDED.ma_nhan_vien_ctxh,
            ma_co_so = EXCLUDED.ma_co_so,
            ten_co_so = EXCLUDED.ten_co_so,
            loai_co_so = EXCLUDED.loai_co_so,
            ngay_bat_dau = EXCLUDED.ngay_bat_dau,
            ngay_ket_thuc = EXCLUDED.ngay_ket_thuc,
            la_cong_tac_hien_tai = EXCLUDED.la_cong_tac_hien_tai,
            trang_thai = EXCLUDED.trang_thai,
            ma_vi_tri = EXCLUDED.ma_vi_tri,
            ten_vi_tri = EXCLUDED.ten_vi_tri,
            ma_loai_hop_dong = EXCLUDED.ma_loai_hop_dong,
            ten_loai_hop_dong = EXCLUDED.ten_loai_hop_dong,
            mo_ta_cong_viec = EXCLUDED.mo_ta_cong_viec,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    return pd.DataFrame([
        {
            "target_table": "public.btxh_fact_lich_su_cong_tac_nhan_vien_ctxh",
            "rows_loaded": matched_rows,
            "loaded_at": execution_time,
        }
    ])