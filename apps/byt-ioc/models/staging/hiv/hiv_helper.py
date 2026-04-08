"""Parsing helpers for the HIV/AIDS staging source."""
from __future__ import annotations

import typing as t

from .._helpers.common import get_address, join_values, parse_date


def flatten_hiv_aids(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a single raw BYT-IOC HivAids record into a wide dict."""
    patient = record.get("nguoiNhiemHIV") or {}
    perm = get_address(patient.get("noiThuongTru"))
    curr = get_address(patient.get("noiOHienTai"))

    ma_tinh_trang = join_values(record.get("dsMaTinhTrangDK") or [], key="maTinhTrangDK")
    ma_xu_tri = join_values(record.get("dsMaXuTri") or [], key="maXuTri")

    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "su_kien": record.get("suKien"),
        "id_ban_ghi": record.get("idBanGhi"),
        "thoi_gian_cap_nhat": record.get("thoiGianCapNhat"),
        "nguon_du_lieu": record.get("nguonDuLieu"),
        "so_dinh_danh": patient.get("soDinhDanh"),
        "ho_va_ten": patient.get("hoVaTen"),
        "ngay_sinh": parse_date(patient.get("ngayThangNamSinh")),
        "gioi_tinh": patient.get("gioiTinh"),
        "dan_toc": patient.get("danToc"),
        "dia_chi_thuong_tru": perm.get("dia_chi_chi_tiet"),
        "ma_xa_thuong_tru": perm.get("ma_xa"),
        "phuong_xa_thuong_tru": perm.get("phuong_xa"),
        "ma_tinh_thuong_tru": perm.get("ma_tinh"),
        "tinh_tp_thuong_tru": perm.get("tinh_tp"),
        "dia_chi_hien_tai": curr.get("dia_chi_chi_tiet"),
        "ma_xa_hien_tai": curr.get("ma_xa"),
        "phuong_xa_hien_tai": curr.get("phuong_xa"),
        "ma_tinh_hien_tai": curr.get("ma_tinh"),
        "tinh_tp_hien_tai": curr.get("tinh_tp"),
        "ngay_kd_hiv": parse_date(record.get("ngayKDHIV")),
        "noi_lay_mau_xn": record.get("noiLayMauXN"),
        "noi_xn_kd": record.get("noiXNKD"),
        "ma_cskc_b": record.get("maCSKCB"),
        "noi_bd_dt_arv": record.get("noiBDDTARV"),
        "ngay_bd_dt_arv": parse_date(record.get("bddtarv")),
        "ma_phac_do_bd": record.get("maPhacDoDieuTriBD"),
        "ma_bac_phac_do_bd": record.get("maBacPhacDoBD"),
        "ma_phac_do_dieu_tri": record.get("maPhacDoDieuTri"),
        "ma_bac_phac_do": record.get("maBacPhacDo"),
        "so_ngay_cap_thuoc_arv": record.get("soNgayCapThuocARV"),
        "ngay_chuyen_phac_do": parse_date(record.get("ngayChuyenPhacDo")),
        "ngay_bd_xu_tri": parse_date(record.get("ngayBDXuTri")),
        "ngay_kt_xu_tri": parse_date(record.get("ngayKTXuTri")),
        "ma_tinh_trang_dk": ma_tinh_trang,
        "ma_xu_tri": ma_xu_tri,
        "loai_dieu_tri_lao": record.get("loaiDieuTriLao"),
        "ngay_bd_dieu_tri_lao": parse_date(record.get("ngayBDDieuTriLao")),
        "ngay_kt_dieu_tri_lao": parse_date(record.get("ngayKTDieuTriLao")),
        "kq_dieu_tri_lao": record.get("kqDieuTriLao"),
        "ma_ly_do_xn_tlvr": record.get("maLyDoXNTLVR"),
        "ngay_xn_tlvr": parse_date(record.get("ngayXNTLVR")),
        "kq_xn_tlvr": record.get("kqXNTLVR"),
        "ngay_kq_xn_tlvr": parse_date(record.get("ngayKQXNTLVR")),
        "ma_loai_bn": record.get("maLoaiBN"),
        "nhom_doi_tuong": record.get("nhomDoiTuong"),
    }