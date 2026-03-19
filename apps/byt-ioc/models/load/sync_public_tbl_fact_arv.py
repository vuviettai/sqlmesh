from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.utils.errors import SQLMeshError


@model(
    "sqlmesh_work.sync_public_tbl_fact_arv",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_tbl_fact_arv",
        "sqlmesh_work.sync_public_tbl_dim_plhiv",
        "sqlmesh_work.sync_public_tbl_dim_co_so",
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

    source_table = context.resolve_table("sqlmesh_work.src_tbl_fact_arv")
    source_rows = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    plhiv_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.tbl_dim_plhiv").iloc[0]["cnt"])
    facility_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.tbl_dim_co_so").iloc[0]["cnt"])

    if source_rows > 0 and plhiv_rows == 0:
        raise SQLMeshError("public.tbl_dim_plhiv is empty, so public.tbl_fact_arv cannot be loaded.")

    if source_rows > 0 and facility_rows == 0:
        raise SQLMeshError("public.tbl_dim_co_so is empty, so public.tbl_fact_arv cannot be loaded.")

    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} AS s
            JOIN public.tbl_dim_plhiv p
              ON p.ma_plhiv = s.ma_plhiv
            JOIN public.tbl_dim_co_so c
              ON c.ma_co_so = s.ma_co_so
            """
        ).iloc[0]["cnt"]
    )

    if source_rows > 0 and matched_rows == 0:
        raise SQLMeshError(
            "No rows from sqlmesh_work.src_tbl_fact_arv match the required BI dimensions public.tbl_dim_plhiv/public.tbl_dim_co_so."
        )

    context.engine_adapter.execute(
        f"""
        DELETE FROM public.tbl_fact_arv AS tgt
        USING {source_table} AS src
        WHERE tgt.ma_plhiv = src.ma_plhiv
          AND tgt.ngay_bat_dau_arv = src.ngay_bat_dau_arv
        """
    )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.tbl_fact_arv (
            ma_plhiv,
            ma_co_so,
            ngay_bat_dau_arv,
            ngay_ket_thuc_arv,
            trang_thai_dieu_tri,
            phac_do,
            kenh_quan_ly
        )
        SELECT
            s.ma_plhiv,
            s.ma_co_so,
            s.ngay_bat_dau_arv,
            s.ngay_ket_thuc_arv,
            s.trang_thai_dieu_tri,
            s.phac_do,
            s.kenh_quan_ly
        FROM {source_table} AS s
        JOIN public.tbl_dim_plhiv p
          ON p.ma_plhiv = s.ma_plhiv
        JOIN public.tbl_dim_co_so c
          ON c.ma_co_so = s.ma_co_so
        """
    )

    return pd.DataFrame(
                [{"target_table": "public.tbl_fact_arv", "rows_loaded": matched_rows, "loaded_at": execution_time}]
    )
