"""Common parsing helpers for BYT-IOC staging models."""
from __future__ import annotations

import typing as t
from datetime import datetime


def parse_date(obj: dict | None) -> str | None:
    """Convert a BYT-IOC date JSON object into an ISO date string."""
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


def parse_iso_date(value: t.Any) -> str | None:
    """Convert a simple date string into ISO date format."""
    if value in (None, ""):
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def parse_epoch_millis(value: t.Any) -> str | None:
    """Convert epoch milliseconds into an ISO timestamp string."""
    if value in (None, ""):
        return None

    try:
        return datetime.utcfromtimestamp(float(value) / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def parse_compact_timestamp(value: t.Any) -> str | None:
    """Convert YYYYMMDDHHMMSS strings into an ISO timestamp string."""
    if value in (None, ""):
        return None

    try:
        return datetime.strptime(str(value), "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def get_address(addr: dict | None) -> dict[str, t.Any]:
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


def join_values(values: t.Any, key: str | None = None) -> str | None:
    """Join list items or list-of-dict field values into a comma-separated string."""
    if not isinstance(values, list):
        return None

    items: list[str] = []
    for value in values:
        if key is None:
            candidate = value
        elif isinstance(value, dict):
            candidate = value.get(key)
        else:
            candidate = None

        if candidate in (None, ""):
            continue
        items.append(str(candidate))

    return ",".join(items) or None


def pick_primary_center_profile(profiles: t.Any) -> dict[str, t.Any]:
    """Pick the most relevant center profile, preferring active and latest admission."""
    if not isinstance(profiles, list) or not profiles:
        return {}

    def sort_key(profile: t.Any) -> tuple[int, str]:
        if not isinstance(profile, dict):
            return (2, "")

        is_active = 0 if profile.get("active") else 1
        admission_date = profile.get("admissionDate") or ""
        return (is_active, str(admission_date))

    return max((profile for profile in profiles if isinstance(profile, dict)), key=sort_key, default={})
