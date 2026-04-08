from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_dim_co_so",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=["sqlmesh_work.src_btxh_dim_co_so"],
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_dim_co_so")
    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_dim_co_so (
            ma_co_so,
            ten_co_so,
            ma_dinh_danh_nguon_co_so,
            da_phat_sinh_ho_so,
            ngay_cap_nhat
        )
        SELECT
            ma_co_so,
            ten_co_so,
            ma_dinh_danh_nguon_co_so,
            da_phat_sinh_ho_so,
            ngay_cap_nhat
        FROM {source_table}
        ON CONFLICT (ma_co_so) DO UPDATE SET
            ten_co_so = EXCLUDED.ten_co_so,
            ma_dinh_danh_nguon_co_so = EXCLUDED.ma_dinh_danh_nguon_co_so,
            da_phat_sinh_ho_so = EXCLUDED.da_phat_sinh_ho_so,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    rows_loaded = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    return pd.DataFrame([
        {"target_table": "public.btxh_dim_co_so", "rows_loaded": rows_loaded, "loaded_at": execution_time}
    ])