from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.utils.errors import SQLMeshError


@model(
    "sqlmesh_work.sync_public_hiv_dim_co_so_mo_rong",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_hiv_dim_co_so_mo_rong",
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

    source_table = context.resolve_table("sqlmesh_work.src_hiv_dim_co_so_mo_rong")
    source_rows = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    parent_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.dim_co_so").iloc[0]["cnt"])

    if source_rows > 0 and parent_rows == 0:
        raise SQLMeshError(
            "public.dim_co_so is empty, so public.hiv_dim_co_so_mo_rong cannot be loaded. "
            "Load the facility dimension first or remove the FK dependency."
        )

    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} AS s
                        JOIN public.dim_co_so c
              ON c.ma_co_so = s.ma_co_so
            """
        ).iloc[0]["cnt"]
    )

    if source_rows > 0 and matched_rows == 0:
        raise SQLMeshError(
            "No rows from sqlmesh_work.src_hiv_dim_co_so_mo_rong match public.dim_co_so.ma_co_so. "
            "Check facility code mapping before loading BI tables."
        )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.hiv_dim_co_so_mo_rong (
            ma_co_so,
            la_co_so_dieu_tri,
            la_co_so_xet_nghiem,
            la_co_so_prep
        )
        SELECT
            s.ma_co_so,
            s.la_co_so_dieu_tri,
            s.la_co_so_xet_nghiem,
            s.la_co_so_prep
        FROM {source_table} AS s
                JOIN public.dim_co_so c
          ON c.ma_co_so = s.ma_co_so
        ON CONFLICT (ma_co_so) DO UPDATE SET
            la_co_so_dieu_tri = EXCLUDED.la_co_so_dieu_tri,
            la_co_so_xet_nghiem = EXCLUDED.la_co_so_xet_nghiem,
            la_co_so_prep = EXCLUDED.la_co_so_prep
        """
    )

    return pd.DataFrame(
        [{"target_table": "public.hiv_dim_co_so_mo_rong", "rows_loaded": matched_rows, "loaded_at": execution_time}]
    )