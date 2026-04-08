from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.utils.errors import SQLMeshError


@model(
    "sqlmesh_work.sync_public_hiv_fact_tai_luong_vi_rut",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_hiv_fact_tai_luong_vi_rut",
        "sqlmesh_work.sync_public_hiv_dim_nguoi_nhiem_hiv",
        "sqlmesh_work.sync_public_hiv_fact_dieu_tri_arv",
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

    source_table = context.resolve_table("sqlmesh_work.src_hiv_fact_tai_luong_vi_rut")
    source_rows = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])

    if source_rows == 0:
        return pd.DataFrame(
            [{"target_table": "public.hiv_fact_tai_luong_vi_rut", "rows_loaded": 0, "loaded_at": execution_time}]
        )

    plhiv_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.hiv_dim_nguoi_nhiem_hiv").iloc[0]["cnt"])
    facility_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.dim_co_so").iloc[0]["cnt"])

    if plhiv_rows == 0:
        raise SQLMeshError("public.hiv_dim_nguoi_nhiem_hiv is empty, so public.hiv_fact_tai_luong_vi_rut cannot be loaded.")

    if facility_rows == 0:
        raise SQLMeshError("public.dim_co_so is empty, so public.hiv_fact_tai_luong_vi_rut cannot be loaded.")

    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} AS s
                                                JOIN public.hiv_dim_nguoi_nhiem_hiv p
                            ON p.ma_nguoi_nhiem_hiv = s.ma_nguoi_nhiem_hiv
                        JOIN public.dim_co_so c
              ON c.ma_co_so = s.ma_co_so
            """
        ).iloc[0]["cnt"]
    )

    if matched_rows == 0:
        raise SQLMeshError(
            "No rows from sqlmesh_work.src_hiv_fact_tai_luong_vi_rut match the required BI dimensions public.hiv_dim_nguoi_nhiem_hiv/public.dim_co_so."
        )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.hiv_fact_tai_luong_vi_rut (
            ma_nguoi_nhiem_hiv,
            ma_co_so,
            ngay_xet_nghiem,
            so_ban_sao_vi_rut,
            la_ket_qua_hop_le,
            thoi_gian_dieu_tri_thang
        )
        SELECT
            s.ma_nguoi_nhiem_hiv,
            s.ma_co_so,
            s.ngay_xet_nghiem,
            s.so_ban_sao_vi_rut,
            s.la_ket_qua_hop_le,
            s.thoi_gian_dieu_tri_thang
        FROM {source_table} AS s
                JOIN public.hiv_dim_nguoi_nhiem_hiv p
          ON p.ma_nguoi_nhiem_hiv = s.ma_nguoi_nhiem_hiv
                JOIN public.dim_co_so c
          ON c.ma_co_so = s.ma_co_so
        ON CONFLICT (ma_nguoi_nhiem_hiv, ngay_xet_nghiem) DO UPDATE SET
            ma_co_so = EXCLUDED.ma_co_so,
            so_ban_sao_vi_rut = EXCLUDED.so_ban_sao_vi_rut,
            la_ket_qua_hop_le = EXCLUDED.la_ket_qua_hop_le,
            thoi_gian_dieu_tri_thang = EXCLUDED.thoi_gian_dieu_tri_thang
        """
    )

    return pd.DataFrame(
        [{"target_table": "public.hiv_fact_tai_luong_vi_rut", "rows_loaded": matched_rows, "loaded_at": execution_time}]
    )