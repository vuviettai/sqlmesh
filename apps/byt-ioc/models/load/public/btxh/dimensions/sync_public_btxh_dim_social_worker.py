from __future__ import annotations

import typing as t
from datetime import datetime

import pandas as pd

from sqlmesh import ExecutionContext, model


@model(
    "sqlmesh_work.sync_public_btxh_dim_nhan_vien_ctxh",
    kind="FULL",
    owner="data_team",
    cron="@daily",
    depends_on=["sqlmesh_work.src_btxh_dim_nhan_vien_ctxh"],
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

    source_table = context.resolve_table("sqlmesh_work.src_btxh_dim_nhan_vien_ctxh")
    context.engine_adapter.execute(
        f"""
        INSERT INTO public.btxh_dim_nhan_vien_ctxh (
            ma_nhan_vien_ctxh,
            ho_va_ten,
            gioi_tinh,
            ngay_sinh,
            ma_dan_toc,
            ten_dan_toc,
            ma_quoc_tich,
            ten_quoc_tich,
            so_dien_thoai,
            thu_dien_tu,
            ma_tinh,
            dia_chi,
            so_giay_to,
            ma_loai_giay_to,
            ten_loai_giay_to,
            ngay_cap_giay_to,
            noi_cap_giay_to,
            ma_to_chuc,
            ma_co_so_hien_tai,
            ten_co_so_hien_tai,
            loai_co_so_hien_tai,
            ma_vi_tri_hien_tai,
            ten_vi_tri_hien_tai,
            ma_loai_hop_dong_hien_tai,
            ten_loai_hop_dong_hien_tai,
            ma_trinh_do_hoc_van,
            ten_trinh_do_hoc_van,
            ma_chuyen_nganh,
            ten_chuyen_nganh,
            nam_tot_nghiep,
            so_lich_su_cong_tac,
            so_lich_su_hoc_van,
            so_chung_chi_hanh_nghe,
            dang_hoat_dong,
            ngay_cap_nhat
        )
        SELECT
            ma_nhan_vien_ctxh,
            ho_va_ten,
            gioi_tinh,
            ngay_sinh,
            ma_dan_toc,
            ten_dan_toc,
            ma_quoc_tich,
            ten_quoc_tich,
            so_dien_thoai,
            thu_dien_tu,
            ma_tinh,
            dia_chi,
            so_giay_to,
            ma_loai_giay_to,
            ten_loai_giay_to,
            ngay_cap_giay_to,
            noi_cap_giay_to,
            ma_to_chuc,
            ma_co_so_hien_tai,
            ten_co_so_hien_tai,
            loai_co_so_hien_tai,
            ma_vi_tri_hien_tai,
            ten_vi_tri_hien_tai,
            ma_loai_hop_dong_hien_tai,
            ten_loai_hop_dong_hien_tai,
            ma_trinh_do_hoc_van,
            ten_trinh_do_hoc_van,
            ma_chuyen_nganh,
            ten_chuyen_nganh,
            nam_tot_nghiep,
            so_lich_su_cong_tac,
            so_lich_su_hoc_van,
            so_chung_chi_hanh_nghe,
            dang_hoat_dong,
            ngay_cap_nhat
        FROM {source_table}
        ON CONFLICT (ma_nhan_vien_ctxh) DO UPDATE SET
            ho_va_ten = EXCLUDED.ho_va_ten,
            gioi_tinh = EXCLUDED.gioi_tinh,
            ngay_sinh = EXCLUDED.ngay_sinh,
            ma_dan_toc = EXCLUDED.ma_dan_toc,
            ten_dan_toc = EXCLUDED.ten_dan_toc,
            ma_quoc_tich = EXCLUDED.ma_quoc_tich,
            ten_quoc_tich = EXCLUDED.ten_quoc_tich,
            so_dien_thoai = EXCLUDED.so_dien_thoai,
            thu_dien_tu = EXCLUDED.thu_dien_tu,
            ma_tinh = EXCLUDED.ma_tinh,
            dia_chi = EXCLUDED.dia_chi,
            so_giay_to = EXCLUDED.so_giay_to,
            ma_loai_giay_to = EXCLUDED.ma_loai_giay_to,
            ten_loai_giay_to = EXCLUDED.ten_loai_giay_to,
            ngay_cap_giay_to = EXCLUDED.ngay_cap_giay_to,
            noi_cap_giay_to = EXCLUDED.noi_cap_giay_to,
            ma_to_chuc = EXCLUDED.ma_to_chuc,
            ma_co_so_hien_tai = EXCLUDED.ma_co_so_hien_tai,
            ten_co_so_hien_tai = EXCLUDED.ten_co_so_hien_tai,
            loai_co_so_hien_tai = EXCLUDED.loai_co_so_hien_tai,
            ma_vi_tri_hien_tai = EXCLUDED.ma_vi_tri_hien_tai,
            ten_vi_tri_hien_tai = EXCLUDED.ten_vi_tri_hien_tai,
            ma_loai_hop_dong_hien_tai = EXCLUDED.ma_loai_hop_dong_hien_tai,
            ten_loai_hop_dong_hien_tai = EXCLUDED.ten_loai_hop_dong_hien_tai,
            ma_trinh_do_hoc_van = EXCLUDED.ma_trinh_do_hoc_van,
            ten_trinh_do_hoc_van = EXCLUDED.ten_trinh_do_hoc_van,
            ma_chuyen_nganh = EXCLUDED.ma_chuyen_nganh,
            ten_chuyen_nganh = EXCLUDED.ten_chuyen_nganh,
            nam_tot_nghiep = EXCLUDED.nam_tot_nghiep,
            so_lich_su_cong_tac = EXCLUDED.so_lich_su_cong_tac,
            so_lich_su_hoc_van = EXCLUDED.so_lich_su_hoc_van,
            so_chung_chi_hanh_nghe = EXCLUDED.so_chung_chi_hanh_nghe,
            dang_hoat_dong = EXCLUDED.dang_hoat_dong,
            ngay_cap_nhat = EXCLUDED.ngay_cap_nhat
        """
    )

    rows_loaded = int(context.fetchdf(f"SELECT COUNT(*) AS cnt FROM {source_table}").iloc[0]["cnt"])
    return pd.DataFrame([
        {"target_table": "public.btxh_dim_nhan_vien_ctxh", "rows_loaded": rows_loaded, "loaded_at": execution_time}
    ])