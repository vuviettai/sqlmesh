from __future__ import annotations

import typing as t

import pandas as pd
from sqlmesh import ExecutionContext, model


MODEL_COLUMNS = {
    "ma_nhan_vien_ctxh": "text",
    "ho_va_ten": "text",
    "gioi_tinh": "text",
    "ngay_sinh": "date",
    "ma_dan_toc": "text",
    "ten_dan_toc": "text",
    "ma_quoc_tich": "text",
    "ten_quoc_tich": "text",
    "so_dien_thoai": "text",
    "thu_dien_tu": "text",
    "ma_tinh": "text",
    "dia_chi": "text",
    "so_giay_to": "text",
    "ma_loai_giay_to": "text",
    "ten_loai_giay_to": "text",
    "ngay_cap_giay_to": "date",
    "noi_cap_giay_to": "text",
    "ma_to_chuc": "text",
    "ma_co_so_hien_tai": "text",
    "ten_co_so_hien_tai": "text",
    "loai_co_so_hien_tai": "text",
    "ma_vi_tri_hien_tai": "text",
    "ten_vi_tri_hien_tai": "text",
    "ma_loai_hop_dong_hien_tai": "text",
    "ten_loai_hop_dong_hien_tai": "text",
    "ma_trinh_do_hoc_van": "text",
    "ten_trinh_do_hoc_van": "text",
    "ma_chuyen_nganh": "text",
    "ten_chuyen_nganh": "text",
    "nam_tot_nghiep": "text",
    "so_lich_su_cong_tac": "int",
    "so_lich_su_hoc_van": "int",
    "so_chung_chi_hanh_nghe": "int",
    "dang_hoat_dong": "boolean",
    "ngay_cap_nhat": "date",
}

QUERY = """
        WITH deduped AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY social_worker_id
                       ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
                   ) AS rn
            FROM {stg_social_workers}
            WHERE social_worker_id IS NOT NULL
        )
        SELECT *
        FROM deduped
        WHERE rn = 1
"""


@model(
    name="public.btxh_dim_nhan_vien_ctxh",
    kind="full",
    columns=MODEL_COLUMNS,
)
def execute(context: ExecutionContext, **kwargs) -> t.Iterator[pd.DataFrame]:
    del kwargs
    df = context.fetchdf(
        QUERY.format(
            stg_social_workers=context.resolve_table("sqlmesh_work.btxh_stg_social_workers")
        )
    )

    if df.empty:
        yield from ()
        return

    result = pd.DataFrame({
        "ma_nhan_vien_ctxh": df["social_worker_id"].astype(str),
        "ho_va_ten": df["ho_va_ten"],
        "gioi_tinh": df["gioi_tinh"],
        "ngay_sinh": pd.to_datetime(df["ngay_sinh"], errors="coerce"),
        "ma_dan_toc": df["ethnicity_code"],
        "ten_dan_toc": df["ethnicity_name"],
        "ma_quoc_tich": df["nationality_code"],
        "ten_quoc_tich": df["nationality_name"],
        "so_dien_thoai": df["phone_number"],
        "thu_dien_tu": df["email"],
        "ma_tinh": df["current_province_code"],
        "dia_chi": df["current_address"],
        "so_giay_to": df["document_number"],
        "ma_loai_giay_to": df["document_type_code"],
        "ten_loai_giay_to": df["document_type_name"],
        "ngay_cap_giay_to": pd.to_datetime(df["document_issue_date"], errors="coerce"),
        "noi_cap_giay_to": df["document_issue_place"],
        "ma_to_chuc": df["organization_id"],
        "ma_co_so_hien_tai": df["current_facility_code"],
        "ten_co_so_hien_tai": df["current_facility_name"],
        "loai_co_so_hien_tai": df["current_facility_type"],
        "ma_vi_tri_hien_tai": df["current_position_code"],
        "ten_vi_tri_hien_tai": df["current_position_name"],
        "ma_loai_hop_dong_hien_tai": df["current_contract_type_code"],
        "ten_loai_hop_dong_hien_tai": df["current_contract_type_name"],
        "ma_trinh_do_hoc_van": df["education_level_code"],
        "ten_trinh_do_hoc_van": df["education_level_name"],
        "ma_chuyen_nganh": df["major_code"],
        "ten_chuyen_nganh": df["major_name"],
        "nam_tot_nghiep": df["graduation_year"],
        "so_lich_su_cong_tac": df["work_history_count"].fillna(0).astype(int),
        "so_lich_su_hoc_van": df["education_history_count"].fillna(0).astype(int),
        "so_chung_chi_hanh_nghe": df["practice_certification_count"].fillna(0).astype(int),
        "dang_hoat_dong": True,
        "ngay_cap_nhat": pd.to_datetime(df["updated_at"], errors="coerce"),
    })

    if result.empty:
        yield from ()
        return

    yield result