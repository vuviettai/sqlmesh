from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_fact_hoat_dong_cham_soc",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=[
        "sqlmesh_work.src_btxh_fact_hoat_dong_cham_soc",
        "sqlmesh_work.sync_public_btxh_dim_nguoi_thu_huong",
        "sqlmesh_work.sync_public_btxh_dim_co_so",
    ],
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_fact_hoat_dong_cham_soc")
    matched_rows = int(
        context.fetchdf(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {source_table} s
            JOIN public.btxh_dim_nguoi_thu_huong b ON b.ma_nguoi_thu_huong = s.ma_nguoi_thu_huong
            LEFT JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
            """
        ).iloc[0]["cnt"]
    )

    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_fact_hoat_dong_cham_soc (
            ma_hoat_dong_cham_soc,
            ma_nguoi_thu_huong,
            ma_co_so,
            ma_ke_hoach_cham_soc,
            trang_thai_ke_hoach_cham_soc,
            ma_muc_tieu,
            mo_ta_muc_tieu,
            muc_do_uu_tien,
            ten_nguoi_quan_ly,
            ten_lanh_dao_co_so,
            trach_nhiem,
            doi_tuong_hoac_nguoi_giam_ho,
            hoat_dong_can_thiep,
            ma_linh_vuc_danh_gia,
            nguon_luc_kinh_phi,
            rui_ro_va_giai_phap,
            dieu_kien_ho_tro,
            ngay_lap_ke_hoach,
            ngay_bat_dau,
            ngay_ket_thuc,
            ngay_phe_duyet,
            ngay_ra_soat,
            so_ke_hoach,
            danh_sach_don_vi_thuc_hien,
            so_don_vi_thuc_hien,
            ngay_cap_nhat
        )
        SELECT
            s.ma_hoat_dong_cham_soc,
            s.ma_nguoi_thu_huong,
            s.ma_co_so,
            s.ma_ke_hoach_cham_soc,
            s.trang_thai_ke_hoach_cham_soc,
            s.ma_muc_tieu,
            s.mo_ta_muc_tieu,
            s.muc_do_uu_tien,
            s.ten_nguoi_quan_ly,
            s.ten_lanh_dao_co_so,
            s.trach_nhiem,
            s.doi_tuong_hoac_nguoi_giam_ho,
            s.hoat_dong_can_thiep,
            s.ma_linh_vuc_danh_gia,
            s.nguon_luc_kinh_phi,
            s.rui_ro_va_giai_phap,
            s.dieu_kien_ho_tro,
            s.ngay_lap_ke_hoach,
            s.ngay_bat_dau,
            s.ngay_ket_thuc,
            s.ngay_phe_duyet,
            s.ngay_ra_soat,
            s.so_ke_hoach,
            s.danh_sach_don_vi_thuc_hien,
            s.so_don_vi_thuc_hien,
            s.ngay_cap_nhat
        FROM {source_table} s
        JOIN public.btxh_dim_nguoi_thu_huong b ON b.ma_nguoi_thu_huong = s.ma_nguoi_thu_huong
        LEFT JOIN public.btxh_dim_co_so f ON f.ma_co_so = s.ma_co_so
        ON CONFLICT (ma_hoat_dong_cham_soc) DO UPDATE SET
            ma_nguoi_thu_huong = EXCLUDED.ma_nguoi_thu_huong,
            ma_co_so = EXCLUDED.ma_co_so,
            ma_ke_hoach_cham_soc = EXCLUDED.ma_ke_hoach_cham_soc,
            trang_thai_ke_hoach_cham_soc = EXCLUDED.trang_thai_ke_hoach_cham_soc,
            ma_muc_tieu = EXCLUDED.ma_muc_tieu,
            mo_ta_muc_tieu = EXCLUDED.mo_ta_muc_tieu,
            muc_do_uu_tien = EXCLUDED.muc_do_uu_tien,
            ten_nguoi_quan_ly = EXCLUDED.ten_nguoi_quan_ly,
            ten_lanh_dao_co_so = EXCLUDED.ten_lanh_dao_co_so,
            trach_nhiem = EXCLUDED.trach_nhiem,
            doi_tuong_hoac_nguoi_giam_ho = EXCLUDED.doi_tuong_hoac_nguoi_giam_ho,
            hoat_dong_can_thiep = EXCLUDED.hoat_dong_can_thiep,
            ma_linh_vuc_danh_gia = EXCLUDED.ma_linh_vuc_danh_gia,
            nguon_luc_kinh_phi = EXCLUDED.nguon_luc_kinh_phi,
            rui_ro_va_giai_phap = EXCLUDED.rui_ro_va_giai_phap,
            dieu_kien_ho_tro = EXCLUDED.dieu_kien_ho_tro,
            ngay_lap_ke_hoach = EXCLUDED.ngay_lap_ke_hoach,
            ngay_bat_dau = EXCLUDED.ngay_bat_dau,
            ngay_ket_thuc = EXCLUDED.ngay_ket_thuc,
            ngay_phe_duyet = EXCLUDED.ngay_phe_duyet,
            ngay_ra_soat = EXCLUDED.ngay_ra_soat,
            so_ke_hoach = EXCLUDED.so_ke_hoach,
            danh_sach_don_vi_thuc_hien = EXCLUDED.danh_sach_don_vi_thuc_hien,
            so_don_vi_thuc_hien = EXCLUDED.so_don_vi_thuc_hien,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    return pd.DataFrame([
        {"target_table": "public.btxh_fact_hoat_dong_cham_soc", "rows_loaded": matched_rows, "loaded_at": execution_time}
    ])