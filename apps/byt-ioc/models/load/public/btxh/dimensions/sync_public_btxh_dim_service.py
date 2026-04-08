from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_dim_dich_vu",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=["sqlmesh_work.src_btxh_dim_dich_vu"],
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_dim_dich_vu")
    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_dim_dich_vu (
            ma_dich_vu,
            ten_dich_vu,
            ngay_cap_nhat
        )
        SELECT
            ma_dich_vu,
            ten_dich_vu,
            ngay_cap_nhat
        FROM {source_table}
        ON CONFLICT (ma_dich_vu) DO UPDATE SET
            ten_dich_vu = EXCLUDED.ten_dich_vu,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    rows_loaded = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    return pd.DataFrame([
        {"target_table": "public.btxh_dim_dich_vu", "rows_loaded": rows_loaded, "loaded_at": execution_time}
    ])