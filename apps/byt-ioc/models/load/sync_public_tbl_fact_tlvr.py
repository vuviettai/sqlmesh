from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model
from sqlmesh.utils.errors import SQLMeshError


@model(
    "sqlmesh_work.sync_public_tbl_fact_tlvr",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_tbl_fact_tlvr",
        "sqlmesh_work.sync_public_tbl_dim_plhiv",
        "sqlmesh_work.sync_public_tbl_fact_arv",
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

    source_table = context.resolve_table("sqlmesh_work.src_tbl_fact_tlvr")
    source_rows = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])

    if source_rows == 0:
        return pd.DataFrame(
            [{"target_table": "public.tbl_fact_tlvr", "rows_loaded": 0, "loaded_at": execution_time}]
        )

    plhiv_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.tbl_dim_plhiv").iloc[0]["cnt"])
    facility_rows = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.tbl_dim_co_so").iloc[0]["cnt"])

    if plhiv_rows == 0:
        raise SQLMeshError("public.tbl_dim_plhiv is empty, so public.tbl_fact_tlvr cannot be loaded.")

    if facility_rows == 0:
        raise SQLMeshError("public.tbl_dim_co_so is empty, so public.tbl_fact_tlvr cannot be loaded.")

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

    if matched_rows == 0:
        raise SQLMeshError(
            "No rows from sqlmesh_work.src_tbl_fact_tlvr match the required BI dimensions public.tbl_dim_plhiv/public.tbl_dim_co_so."
        )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.tbl_fact_tlvr (
            ma_plhiv,
            ma_co_so,
            ngay_xet_nghiem,
            ket_qua_copies,
            la_ket_qua_hop_le,
            thoi_gian_dieu_tri_thang
        )
        SELECT
            s.ma_plhiv,
            s.ma_co_so,
            s.ngay_xet_nghiem,
            s.ket_qua_copies,
            s.la_ket_qua_hop_le,
            s.thoi_gian_dieu_tri_thang
        FROM {source_table} AS s
        JOIN public.tbl_dim_plhiv p
          ON p.ma_plhiv = s.ma_plhiv
        JOIN public.tbl_dim_co_so c
          ON c.ma_co_so = s.ma_co_so
        ON CONFLICT (ma_plhiv, ngay_xet_nghiem) DO UPDATE SET
            ma_co_so = EXCLUDED.ma_co_so,
            ket_qua_copies = EXCLUDED.ket_qua_copies,
            la_ket_qua_hop_le = EXCLUDED.la_ket_qua_hop_le,
            thoi_gian_dieu_tri_thang = EXCLUDED.thoi_gian_dieu_tri_thang
        """
    )

    return pd.DataFrame(
        [{"target_table": "public.tbl_fact_tlvr", "rows_loaded": matched_rows, "loaded_at": execution_time}]
    )