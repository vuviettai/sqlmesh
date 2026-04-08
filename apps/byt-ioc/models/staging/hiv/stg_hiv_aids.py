"""Transform records from staging_db.HivAids into sqlmesh_work.stg_hiv_aids."""
from __future__ import annotations

import os
import typing as t
from datetime import datetime

import pandas as pd
from psycopg2 import sql

from sqlmesh import ExecutionContext, model
from sqlmesh.core.model.kind import ModelKindName

from .._helpers.db import get_connection
from .._helpers.env import load_dotenv_if_present
from .hiv_helper import flatten_hiv_aids


MODEL_COLUMNS = {
    "_airbyte_raw_id": "text",
    "_airbyte_extracted_at": "timestamptz",
    "_airbyte_generation_id": "bigint",
    "su_kien": "text",
    "id_ban_ghi": "text",
    "thoi_gian_cap_nhat": "timestamp",
    "nguon_du_lieu": "text",
    "so_dinh_danh": "text",
    "ho_va_ten": "text",
    "ngay_sinh": "date",
    "gioi_tinh": "text",
    "dan_toc": "text",
    "dia_chi_thuong_tru": "text",
    "ma_xa_thuong_tru": "text",
    "phuong_xa_thuong_tru": "text",
    "ma_tinh_thuong_tru": "text",
    "tinh_tp_thuong_tru": "text",
    "dia_chi_hien_tai": "text",
    "ma_xa_hien_tai": "text",
    "phuong_xa_hien_tai": "text",
    "ma_tinh_hien_tai": "text",
    "tinh_tp_hien_tai": "text",
    "ngay_kd_hiv": "date",
    "noi_lay_mau_xn": "text",
    "noi_xn_kd": "text",
    "ma_cskc_b": "text",
    "noi_bd_dt_arv": "text",
    "ngay_bd_dt_arv": "date",
    "ma_phac_do_bd": "text",
    "ma_bac_phac_do_bd": "text",
    "ma_phac_do_dieu_tri": "text",
    "ma_bac_phac_do": "text",
    "so_ngay_cap_thuoc_arv": "double",
    "ngay_chuyen_phac_do": "date",
    "ngay_bd_xu_tri": "date",
    "ngay_kt_xu_tri": "date",
    "ma_tinh_trang_dk": "text",
    "ma_xu_tri": "text",
    "loai_dieu_tri_lao": "text",
    "ngay_bd_dieu_tri_lao": "date",
    "ngay_kt_dieu_tri_lao": "date",
    "kq_dieu_tri_lao": "text",
    "ma_ly_do_xn_tlvr": "text",
    "ngay_xn_tlvr": "date",
    "kq_xn_tlvr": "text",
    "ngay_kq_xn_tlvr": "date",
    "ma_loai_bn": "text",
    "nhom_doi_tuong": "text",
}

DATE_COLUMNS = (
    "ngay_sinh",
    "ngay_kd_hiv",
    "ngay_bd_dt_arv",
    "ngay_chuyen_phac_do",
    "ngay_bd_xu_tri",
    "ngay_kt_xu_tri",
    "ngay_bd_dieu_tri_lao",
    "ngay_kt_dieu_tri_lao",
    "ngay_xn_tlvr",
    "ngay_kq_xn_tlvr",
)

FETCH_BATCH_SIZE = 10_000


def _normalize_dataframe(records: list[dict[str, t.Any]]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records)
    df = df.reindex(columns=MODEL_COLUMNS.keys())
    df["_airbyte_extracted_at"] = pd.to_datetime(df["_airbyte_extracted_at"], errors="coerce")
    df["thoi_gian_cap_nhat"] = pd.to_datetime(df["thoi_gian_cap_nhat"], errors="coerce")

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    df["_airbyte_generation_id"] = pd.to_numeric(df["_airbyte_generation_id"], errors="coerce").astype("Int64")
    df["so_ngay_cap_thuoc_arv"] = pd.to_numeric(df["so_ngay_cap_thuoc_arv"], errors="coerce")
    return df.astype(object).where(pd.notna(df), None)


@model(
    "sqlmesh_work.stg_hiv_aids",
    description=(
        "Cleaned and flattened HIV/AIDS records from the staging PostgreSQL "
        "table public.HivAids into the BI PostgreSQL database."
    ),
    kind=dict(name=ModelKindName.INCREMENTAL_BY_TIME_RANGE, time_column="thoi_gian_cap_nhat", batch_size=90),
    start="2020-01-01",
    cron="@daily",
    owner="data_team",
    grain=["id_ban_ghi"],
    columns=MODEL_COLUMNS,
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> t.Iterator[pd.DataFrame]:
    del context, execution_time, kwargs

    load_dotenv_if_present()
    conn = get_connection()
    try:
        schema_name = os.environ.get("STAGING_DB_SCHEMA", "public")
        table_name = os.environ.get("STAGING_SOURCE_TABLE", "HivAids")
        query = sql.SQL(
            """
            SELECT
                _airbyte_raw_id,
                _airbyte_extracted_at,
                _airbyte_generation_id,
                \"suKien\",
                bddtarv,
                \"maCSKCB\",
                \"noiXNKD\",
                \"idBanGhi\",
                \"kqXNTLVR\",
                \"maLoaiBN\",
                \"dsMaXuTri\",
                \"ngayKDHIV\",
                \"ngayXNTLVR\",
                \"noiBDDTARV\",
                \"maBacPhacDo\",
                \"ngayBDXuTri\",
                \"ngayKTXuTri\",
                \"nguonDuLieu\",
                \"noiLayMauXN\",
                \"kqDieuTriLao\",
                \"maLyDoXNTLVR\",
                \"ngayKQXNTLVR\",
                \"nhomDoiTuong\",
                \"maBacPhacDoBD\",
                \"nguoiNhiemHIV\",
                \"loaiDieuTriLao\",
                \"dsMaTinhTrangDK\",
                \"maPhacDoDieuTri\",
                \"thoiGianCapNhat\",
                \"ngayBDDieuTriLao\",
                \"ngayChuyenPhacDo\",
                \"ngayKTDieuTriLao\",
                \"maPhacDoDieuTriBD\",
                \"soNgayCapThuocARV\"
            FROM {schema}.{table}
            WHERE NULLIF(\"thoiGianCapNhat\", '')::timestamp >= %(start)s
              AND NULLIF(\"thoiGianCapNhat\", '')::timestamp < %(end)s
            """
        ).format(schema=sql.Identifier(schema_name), table=sql.Identifier(table_name))

        with conn.cursor() as cur:
            cur.execute(query, {"start": start, "end": end})
            while True:
                rows = cur.fetchmany(FETCH_BATCH_SIZE)
                if not rows:
                    break

                records = [flatten_hiv_aids(dict(row)) for row in rows]
                yield _normalize_dataframe(records)
    finally:
        conn.close()
