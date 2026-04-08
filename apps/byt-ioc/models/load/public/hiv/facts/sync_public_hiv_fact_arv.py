from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.utils.errors import SQLMeshError


@model(
    "sqlmesh_work.sync_public_hiv_fact_dieu_tri_arv",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_hiv_fact_dieu_tri_arv",
        "sqlmesh_work.sync_public_hiv_dim_nguoi_nhiem_hiv",
        "sqlmesh_work.sync_public_shared_dim_co_so",
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

    source_table = context.resolve_table("sqlmesh_work.src_hiv_fact_dieu_tri_arv")
    source_rows = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    plhiv_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.hiv_dim_nguoi_nhiem_hiv").iloc[0]["cnt"])
    facility_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.dim_co_so").iloc[0]["cnt"])

    if source_rows > 0 and plhiv_rows == 0:
        raise SQLMeshError("public.hiv_dim_nguoi_nhiem_hiv is empty, so public.hiv_fact_dieu_tri_arv cannot be loaded.")

    if source_rows > 0 and facility_rows == 0:
        raise SQLMeshError("public.dim_co_so is empty, so public.hiv_fact_dieu_tri_arv cannot be loaded.")

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

    if source_rows > 0 and matched_rows == 0:
        raise SQLMeshError(
            "No rows from sqlmesh_work.src_hiv_fact_dieu_tri_arv match the required BI dimensions public.hiv_dim_nguoi_nhiem_hiv/public.dim_co_so."
        )

    context.engine_adapter.execute(
        f"""
                DELETE FROM public.hiv_fact_dieu_tri_arv AS tgt
        USING {source_table} AS src
            WHERE tgt.ma_nguoi_nhiem_hiv = src.ma_nguoi_nhiem_hiv
          AND tgt.ngay_bat_dau_arv = src.ngay_bat_dau_arv
        """
    )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.hiv_fact_dieu_tri_arv (
            ma_nguoi_nhiem_hiv,
            ma_co_so,
            ngay_bat_dau_arv,
            ngay_ket_thuc_arv,
            trang_thai_dieu_tri,
            phac_do,
            kenh_quan_ly
        )
        SELECT
            s.ma_nguoi_nhiem_hiv,
            s.ma_co_so,
            s.ngay_bat_dau_arv,
            s.ngay_ket_thuc_arv,
            s.trang_thai_dieu_tri,
            s.phac_do,
            s.kenh_quan_ly
        FROM {source_table} AS s
                JOIN public.hiv_dim_nguoi_nhiem_hiv p
          ON p.ma_nguoi_nhiem_hiv = s.ma_nguoi_nhiem_hiv
                JOIN public.dim_co_so c
          ON c.ma_co_so = s.ma_co_so
        """
    )

    return pd.DataFrame(
        [{"target_table": "public.hiv_fact_dieu_tri_arv", "rows_loaded": matched_rows, "loaded_at": execution_time}]
    )