from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_shared_don_vi_hanh_chinh",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=["sqlmesh_work.stg_hiv_aids"],
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
        UPDATE public.don_vi_hanh_chinh d
        SET ten_tinh = src.ten_tinh,
            updated_at = CURRENT_TIMESTAMP
        FROM (
            SELECT
                ma_tinh,
                MAX(ten_tinh) AS ten_tinh
            FROM (
                SELECT
                    LPAD(REGEXP_REPLACE(COALESCE(ma_tinh_hien_tai, ma_tinh_thuong_tru), '[^0-9]', '', 'g'), 2, '0') AS ma_tinh,
                    NULLIF(TRIM(COALESCE(tinh_tp_hien_tai, tinh_tp_thuong_tru)), '') AS ten_tinh
                FROM {stg_table}
                WHERE COALESCE(ma_tinh_hien_tai, ma_tinh_thuong_tru) IS NOT NULL
            ) x
            WHERE ma_tinh IS NOT NULL
            GROUP BY ma_tinh
        ) src
        WHERE d.ma_tinh_thanh = src.ma_tinh
          AND src.ten_tinh IS NOT NULL
        """
    )

    context.engine_adapter.execute(
        f"""
        WITH src AS (
            SELECT
                ma_tinh,
                COALESCE(MAX(ten_tinh), 'KHONG_XAC_DINH') AS ten_tinh
            FROM (
                SELECT
                    LPAD(REGEXP_REPLACE(COALESCE(ma_tinh_hien_tai, ma_tinh_thuong_tru), '[^0-9]', '', 'g'), 2, '0') AS ma_tinh,
                    NULLIF(TRIM(COALESCE(tinh_tp_hien_tai, tinh_tp_thuong_tru)), '') AS ten_tinh
                FROM {stg_table}
                WHERE COALESCE(ma_tinh_hien_tai, ma_tinh_thuong_tru) IS NOT NULL
            ) x
            WHERE ma_tinh IS NOT NULL
            GROUP BY ma_tinh
        ),
        missing AS (
            SELECT s.*
            FROM src s
            LEFT JOIN public.don_vi_hanh_chinh d
              ON d.ma_tinh_thanh = s.ma_tinh
            WHERE d.ma_tinh_thanh IS NULL
        ),
        base AS (
            SELECT COALESCE(MAX(id), 0) AS max_id FROM public.don_vi_hanh_chinh
        )
        INSERT INTO public.don_vi_hanh_chinh (
            id,
            ma_tinh_thanh,
            ten_tinh,
            ma_tinh_thanh_tms,
            ma_quan_huyen_tms,
            ten_quan_huyen_tms,
            ma_phuong_xa,
            ten_phuong_xa,
            created_at,
            updated_at
        )
        SELECT
            base.max_id + ROW_NUMBER() OVER (ORDER BY m.ma_tinh) AS id,
            m.ma_tinh,
            m.ten_tinh,
            m.ma_tinh,
            '000',
            'KHONG_XAC_DINH',
            '00000',
            'KHONG_XAC_DINH',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM missing m
        CROSS JOIN base
        """
    )

    rows_loaded = int(context.fetchdf("SELECT COUNT(*) AS cnt FROM public.don_vi_hanh_chinh").iloc[0]["cnt"])
    return pd.DataFrame(
        [{"target_table": "public.don_vi_hanh_chinh", "rows_loaded": rows_loaded, "loaded_at": execution_time}]
    )