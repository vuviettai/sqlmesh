from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.utils.errors import SQLMeshError


@model(
    "sqlmesh_work.sync_public_hiv_dim_nguoi_nhiem_hiv",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_hiv_dim_nguoi_nhiem_hiv",
        "sqlmesh_work.sync_public_shared_don_vi_hanh_chinh",
    ],
    columns={
        "target_table": "text",
        "rows_loaded": "bigint",
        "loaded_at": "timestamp",
    },
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> pd.DataFrame:
    del start, end, kwargs

    source_table = context.resolve_table("sqlmesh_work.src_hiv_dim_nguoi_nhiem_hiv")
    source_rows = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    parent_rows = int(
        context.fetchdf("SELECT COUNT(*) AS cnt FROM public.don_vi_hanh_chinh").iloc[0]["cnt"]
    )

    if source_rows > 0 and parent_rows == 0:
        raise SQLMeshError(
            "public.don_vi_hanh_chinh is empty, so public.hiv_dim_nguoi_nhiem_hiv cannot be loaded. "
            "Load the administrative dimension first or remove the FK dependency."
        )

    matched_rows = int(
        context.fetchdf(
            f"""
                        SELECT COUNT(*) AS cnt
            FROM {source_table} AS s
            JOIN public.don_vi_hanh_chinh dvhc
                            ON dvhc.ma_tinh_thanh = LPAD(REGEXP_REPLACE(s.ma_tinh, '[^0-9]', '', 'g'), 2, '0')
            """
        ).iloc[0]["cnt"]
    )

    if source_rows > 0 and matched_rows == 0:
        raise SQLMeshError(
            "No rows from sqlmesh_work.src_hiv_dim_nguoi_nhiem_hiv match public.don_vi_hanh_chinh.ma_tinh_thanh. "
            "Check province code mapping before loading BI tables."
        )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.hiv_dim_nguoi_nhiem_hiv (
            ma_nguoi_nhiem_hiv,
            gioi_tinh,
            nhom_tuoi,
            ma_tinh,
            nhom_nguy_co,
            duong_lay,
            ngay_chan_doan,
            trang_thai,
            ngay_tu_vong,
            kenh_phat_hien,
            ngay_cap_nhat
        )
        SELECT
            s.ma_nguoi_nhiem_hiv,
            s.gioi_tinh,
            s.nhom_tuoi,
            LPAD(REGEXP_REPLACE(s.ma_tinh, '[^0-9]', '', 'g'), 2, '0') AS ma_tinh,
            s.nhom_nguy_co,
            s.duong_lay,
            s.ngay_chan_doan,
            s.trang_thai,
            s.ngay_tu_vong,
            s.kenh_phat_hien,
            s.ngay_cap_nhat
        FROM {source_table} AS s
        JOIN public.don_vi_hanh_chinh dvhc
                    ON dvhc.ma_tinh_thanh = LPAD(REGEXP_REPLACE(s.ma_tinh, '[^0-9]', '', 'g'), 2, '0')
        ON CONFLICT (ma_nguoi_nhiem_hiv) DO UPDATE SET
            gioi_tinh = EXCLUDED.gioi_tinh,
            nhom_tuoi = EXCLUDED.nhom_tuoi,
            ma_tinh = EXCLUDED.ma_tinh,
            nhom_nguy_co = EXCLUDED.nhom_nguy_co,
            duong_lay = EXCLUDED.duong_lay,
            ngay_chan_doan = EXCLUDED.ngay_chan_doan,
            trang_thai = EXCLUDED.trang_thai,
            ngay_tu_vong = EXCLUDED.ngay_tu_vong,
            kenh_phat_hien = EXCLUDED.kenh_phat_hien,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    return pd.DataFrame(
        [{"target_table": "public.hiv_dim_nguoi_nhiem_hiv", "rows_loaded": matched_rows, "loaded_at": execution_time}]
    )