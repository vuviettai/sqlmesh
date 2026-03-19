"""Parsing and flattening helpers for BYT-IOC HivAids records."""
from __future__ import annotations

import typing as t
from datetime import datetime


def parse_date(obj: dict | None) -> str | None:
    """Convert a BYT-IOC date JSON object into an ISO date string (YYYY-MM-DD).

    The object may carry:
    - ngayThangNam: full date  (preferred)
    - thangNam:     year-month (returns 1st of month)
    - nam:          year only  (returns Jan 1st of year)
    """
    if not obj or not isinstance(obj, dict):
        return None

    ngay = obj.get("ngayThangNam")
    if ngay:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(ngay, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass

    thang = obj.get("thangNam")
    if thang:
        for fmt in ("%Y-%m", "%m/%Y"):
            try:
                return datetime.strptime(thang, fmt).strftime("%Y-%m-01")
            except ValueError:
                pass

    nam = obj.get("nam")
    if nam:
        try:
            return f"{int(nam):04d}-01-01"
        except (ValueError, TypeError):
            pass

    return None


def get_address(addr: dict | None) -> dict:
    """Extract address fields from a BYT-IOC address sub-object."""
    if not addr or not isinstance(addr, dict):
        return {}
    return {
        "dia_chi_chi_tiet": addr.get("diaChiChiTiet"),
        "ma_xa": addr.get("maXa"),
        "phuong_xa": addr.get("phuongXa"),
        "ma_tinh": addr.get("maTinh"),
        "tinh_tp": addr.get("tinhTP"),
        "quoc_gia": addr.get("quocGia"),
    }


def flatten(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a single raw BYT-IOC HivAids record into a wide dict.

    Handles:
    - nguoiNhiemHIV  → patient demographics + addresses
    - dsMaTinhTrangDK / dsMaXuTri → comma-separated code lists
    - All date JSON objects  → ISO date strings via parse_date()
    """
    patient = record.get("nguoiNhiemHIV") or {}
    perm = get_address(patient.get("noiThuongTru"))
    curr = get_address(patient.get("noiOHienTai"))

    tinh_trang = record.get("dsMaTinhTrangDK") or []
    ma_tinh_trang = ",".join(
        item["maTinhTrangDK"]
        for item in tinh_trang
        if item and item.get("maTinhTrangDK")
    )

    xu_tri = record.get("dsMaXuTri") or []
    ma_xu_tri = ",".join(
        item["maXuTri"] for item in xu_tri if item and item.get("maXuTri")
    )

    return {
        # Airbyte metadata
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        # Record metadata
        "su_kien": record.get("suKien"),
        "id_ban_ghi": record.get("idBanGhi"),
        "thoi_gian_cap_nhat": record.get("thoiGianCapNhat"),
        "nguon_du_lieu": record.get("nguonDuLieu"),
        # Patient demographics
        "so_dinh_danh": patient.get("soDinhDanh"),
        "ho_va_ten": patient.get("hoVaTen"),
        "ngay_sinh": parse_date(patient.get("ngayThangNamSinh")),
        "gioi_tinh": patient.get("gioiTinh"),
        "dan_toc": patient.get("danToc"),
        # Permanent residence
        "dia_chi_thuong_tru": perm.get("dia_chi_chi_tiet"),
        "ma_xa_thuong_tru": perm.get("ma_xa"),
        "phuong_xa_thuong_tru": perm.get("phuong_xa"),
        "ma_tinh_thuong_tru": perm.get("ma_tinh"),
        "tinh_tp_thuong_tru": perm.get("tinh_tp"),
        # Current residence
        "dia_chi_hien_tai": curr.get("dia_chi_chi_tiet"),
        "ma_xa_hien_tai": curr.get("ma_xa"),
        "phuong_xa_hien_tai": curr.get("phuong_xa"),
        "ma_tinh_hien_tai": curr.get("ma_tinh"),
        "tinh_tp_hien_tai": curr.get("tinh_tp"),
        # HIV confirmation
        "ngay_kd_hiv": parse_date(record.get("ngayKDHIV")),
        "noi_lay_mau_xn": record.get("noiLayMauXN"),
        "noi_xn_kd": record.get("noiXNKD"),
        "ma_cskc_b": record.get("maCSKCB"),
        # ARV treatment
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
        "ma_tinh_trang_dk": ma_tinh_trang or None,
        "ma_xu_tri": ma_xu_tri or None,
        # TB co-treatment
        "loai_dieu_tri_lao": record.get("loaiDieuTriLao"),
        "ngay_bd_dieu_tri_lao": parse_date(record.get("ngayBDDieuTriLao")),
        "ngay_kt_dieu_tri_lao": parse_date(record.get("ngayKTDieuTriLao")),
        "kq_dieu_tri_lao": record.get("kqDieuTriLao"),
        # Viral load
        "ma_ly_do_xn_tlvr": record.get("maLyDoXNTLVR"),
        "ngay_xn_tlvr": parse_date(record.get("ngayXNTLVR")),
        "kq_xn_tlvr": record.get("kqXNTLVR"),
        "ngay_kq_xn_tlvr": parse_date(record.get("ngayKQXNTLVR")),
        # Classification
        "ma_loai_bn": record.get("maLoaiBN"),
        "nhom_doi_tuong": record.get("nhomDoiTuong"),
    }
