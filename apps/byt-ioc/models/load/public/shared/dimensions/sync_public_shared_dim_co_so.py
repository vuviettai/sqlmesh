from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_shared_dim_co_so",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.stg_hiv_aids",
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

    stg_table = context.resolve_table("sqlmesh_work.stg_hiv_aids")

    context.engine_adapter.execute(
        f"""
        UPDATE public.dim_co_so d
        SET ma_tinh = src.ma_tinh,
            ngay_cap_nhat = CURRENT_DATE
        FROM (
            SELECT
                ma_co_so,
                MIN(ma_tinh) AS ma_tinh
            FROM (
                SELECT
                    COALESCE(noi_bd_dt_arv, ma_cskc_b) AS ma_co_so,
                    LPAD(REGEXP_REPLACE(COALESCE(ma_tinh_hien_tai, ma_tinh_thuong_tru), '[^0-9]', '', 'g'), 2, '0') AS ma_tinh
                FROM {stg_table}
                WHERE COALESCE(noi_bd_dt_arv, ma_cskc_b) IS NOT NULL
            ) x
            WHERE ma_tinh IS NOT NULL
            GROUP BY ma_co_so
        ) src
        WHERE d.ma_co_so = src.ma_co_so
        """
    )

    context.engine_adapter.execute(
        f"""
        WITH src AS (
            SELECT
                ma_co_so,
                COALESCE(MIN(ma_tinh), '00') AS ma_tinh
            FROM (
                SELECT
                    COALESCE(noi_bd_dt_arv, ma_cskc_b) AS ma_co_so,
                    LPAD(REGEXP_REPLACE(COALESCE(ma_tinh_hien_tai, ma_tinh_thuong_tru), '[^0-9]', '', 'g'), 2, '0') AS ma_tinh
                FROM {stg_table}
                WHERE COALESCE(noi_bd_dt_arv, ma_cskc_b) IS NOT NULL
            ) x
            GROUP BY ma_co_so
        ),
        missing AS (
            SELECT s.*
            FROM src s
            LEFT JOIN public.dim_co_so d
              ON d.ma_co_so = s.ma_co_so
            WHERE d.ma_co_so IS NULL
        ),
        base AS (
            SELECT COALESCE(MAX(id), 0) AS max_id FROM public.dim_co_so
        )
        INSERT INTO public.dim_co_so (
            id,
            ma_co_so,
            ten_co_so,
            ma_tinh,
            tuyen,
            loai_co_so,
            loai_hinh,
            ngay_cap_nhat
        )
        SELECT
            base.max_id + ROW_NUMBER() OVER (ORDER BY m.ma_co_so) AS id,
            m.ma_co_so,
            'CO_SO_' || m.ma_co_so,
            m.ma_tinh,
            'TINH',
            NULL,
            'CONG',
            CURRENT_DATE
        FROM missing m
        CROSS JOIN base
        """
    )

    rows_loaded = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.dim_co_so").iloc[0]["cnt"])
    return pd.DataFrame(
        [{"target_table": "public.dim_co_so", "rows_loaded": rows_loaded, "loaded_at": execution_time}]
    )