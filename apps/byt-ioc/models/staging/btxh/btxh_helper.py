"""Parsing helpers for BTXH staging sources."""
from __future__ import annotations

import typing as t

from .._helpers.common import (
    join_values,
    parse_compact_timestamp,
    parse_epoch_millis,
    parse_iso_date,
    pick_primary_center_profile,
)


def _pick_current_work_history(work_histories: t.Any) -> dict[str, t.Any]:
    if not isinstance(work_histories, list) or not work_histories:
        return {}

    current_items = [item for item in work_histories if isinstance(item, dict) and item.get("isCurrent")]
    if current_items:
        return current_items[0]

    return next((item for item in work_histories if isinstance(item, dict)), {})


def flatten_beneficiary(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH beneficiary record into a current-state staging row."""
    residence = record.get("residence") or {}
    paper_identity = record.get("paperIdentity") or {}
    center_profiles = record.get("centerProfiles") or []
    primary_profile = pick_primary_center_profile(center_profiles)

    gender_code = record.get("gender")
    try:
        gender_int = int(gender_code) if gender_code is not None else None
    except (TypeError, ValueError):
        gender_int = None

    gender_label = {1: "NAM", 2: "NU"}.get(gender_int, "KHONG_XAC_DINH")

    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "beneficiary_id": record.get("id"),
        "is_active": record.get("active"),
        "gioi_tinh_ma": gender_int,
        "gioi_tinh": gender_label,
        "su_kien": record.get("suKien"),
        "ho_va_ten": record.get("fullName"),
        "phien_ban": record.get("phienBan"),
        "created_at": parse_epoch_millis(record.get("createdAt")) or parse_compact_timestamp(record.get("createdAtmm")),
        "updated_at": parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm")),
        "created_at_nguon": record.get("createdAtmm"),
        "updated_at_nguon": record.get("updatedAtmm"),
        "ngay_sinh": parse_iso_date(record.get("dateOfBirth")),
        "dan_toc": record.get("ethnicity"),
        "quoc_tich": record.get("nationality"),
        "noi_sinh": record.get("placeOfOrigin"),
        "so_giay_to": paper_identity.get("identityNumber"),
        "ma_loai_giay_to": paper_identity.get("identityTypeCode"),
        "noi_cap_giay_to": paper_identity.get("issuedPlace"),
        "ngay_cap_giay_to": parse_epoch_millis(paper_identity.get("issuedDate")),
        "dia_chi_hien_tai": residence.get("currentAddress"),
        "ma_xa_hien_tai": residence.get("currentWardCode"),
        "ma_tinh_hien_tai": residence.get("currentProvinceCode"),
        "dia_chi_moi": residence.get("newAddress"),
        "ma_xa_moi": residence.get("newWardCode"),
        "ma_tinh_moi": residence.get("newProvinceCode"),
        "co_ho_so_trung_tam": bool(center_profiles),
        "so_ho_so_trung_tam": len(center_profiles) if isinstance(center_profiles, list) else 0,
        "so_ho_so_trung_tam_hoat_dong": sum(
            1 for profile in center_profiles if isinstance(profile, dict) and profile.get("active")
        ) if isinstance(center_profiles, list) else 0,
        "center_profile_id": primary_profile.get("id"),
        "ma_co_so_hien_tai": primary_profile.get("facilityCode"),
        "ten_co_so_hien_tai": primary_profile.get("facilityName"),
        "facility_id": primary_profile.get("facilityId"),
        "ma_trang_thai_ho_so": primary_profile.get("status"),
        "loai_luu_tru": primary_profile.get("stayType"),
        "ngay_tiep_nhan": parse_iso_date(primary_profile.get("admissionDate")),
        "ngay_quyet_dinh_tiep_nhan": parse_iso_date(primary_profile.get("admissionDecisionDate")),
        "so_quyet_dinh_tiep_nhan": primary_profile.get("admissionDecisionNumber") or primary_profile.get("decisionNumber"),
        "co_so_ban_hanh_quyet_dinh": primary_profile.get("admissionDecisionAuthority"),
        "ma_nhom_doi_tuong_chinh": primary_profile.get("objectTypeCode"),
        "danh_sach_ma_nhom_doi_tuong": join_values(primary_profile.get("objectTypeCodes")),
        "danh_sach_ma_dich_vu": join_values(
            primary_profile.get("services").split(",") if isinstance(primary_profile.get("services"), str) else primary_profile.get("services")
        ),
        "danh_sach_dich_vu": join_values(primary_profile.get("providedServices")),
    }


def explode_beneficiary_center_profiles(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH center profiles into one row per beneficiary profile."""
    center_profiles = record.get("centerProfiles") or []
    if not isinstance(center_profiles, list) or not center_profiles:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))

    rows: list[dict[str, t.Any]] = []
    for profile in center_profiles:
        if not isinstance(profile, dict):
            continue

        services = profile.get("services")
        service_codes = services.split(",") if isinstance(services, str) else services
        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "beneficiary_id": record.get("id"),
                "updated_at": updated_at,
                "center_profile_id": profile.get("id"),
                "profile_active": profile.get("active"),
                "profile_deleted": profile.get("deleted"),
                "ma_trang_thai_ho_so": profile.get("status"),
                "ma_co_so": profile.get("facilityCode"),
                "ten_co_so": profile.get("facilityName"),
                "facility_id": profile.get("facilityId"),
                "loai_luu_tru": profile.get("stayType"),
                "ngay_tiep_nhan": parse_iso_date(profile.get("admissionDate")),
                "ngay_quyet_dinh_tiep_nhan": parse_iso_date(profile.get("admissionDecisionDate")),
                "so_quyet_dinh_tiep_nhan": profile.get("admissionDecisionNumber"),
                "co_so_ban_hanh_quyet_dinh": profile.get("admissionDecisionAuthority"),
                "so_quyet_dinh": profile.get("decisionNumber"),
                "ma_nhom_doi_tuong_chinh": profile.get("objectTypeCode"),
                "ma_nhom_doi_tuong": join_values(profile.get("objectTypeCodes")),
                "ma_chi_tiet_doi_tuong": join_values(profile.get("objectDetailCodes")),
                "ma_dich_vu": join_values(service_codes),
                "ten_dich_vu": join_values(profile.get("providedServices")),
                "so_phong": profile.get("roomNumber"),
            }
        )

    return rows


def flatten_care_activity(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH care activity record into one row per care plan activity."""
    person = record.get("person") or {}
    care_plan = record.get("carePlan") or {}
    center_profiles = person.get("centerProfiles") or []
    primary_profile = pick_primary_center_profile(center_profiles)

    gender_code = person.get("gender")
    try:
        gender_int = int(gender_code) if gender_code is not None else None
    except (TypeError, ValueError):
        gender_int = None

    gender_label = {1: "NAM", 2: "NU"}.get(gender_int, "KHONG_XAC_DINH")
    implementing_units = care_plan.get("implementingUnits")

    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "care_activity_id": record.get("id"),
        "beneficiary_id": person.get("id") or care_plan.get("personId"),
        "su_kien": record.get("suKien"),
        "phien_ban": record.get("phienBan"),
        "created_at": parse_compact_timestamp(record.get("createdAtmm")),
        "updated_at": parse_compact_timestamp(record.get("updatedAtmm")),
        "ho_va_ten": person.get("fullName") or care_plan.get("beneficiaryName"),
        "gioi_tinh_ma": gender_int,
        "gioi_tinh": gender_label,
        "ngay_sinh": parse_iso_date(person.get("dateOfBirth")),
        "quoc_tich": person.get("nationality"),
        "center_profile_id": primary_profile.get("id"),
        "ma_co_so": primary_profile.get("facilityCode"),
        "ten_co_so": primary_profile.get("facilityName"),
        "facility_id": primary_profile.get("facilityId"),
        "care_plan_id": care_plan.get("id"),
        "care_plan_status": care_plan.get("status"),
        "goal_code": care_plan.get("goalCode"),
        "goal_description": care_plan.get("goalDescription"),
        "priority_level": care_plan.get("priorityLevel"),
        "manager_name": care_plan.get("managerName"),
        "facility_leader_name": care_plan.get("facilityLeaderName"),
        "responsibility": care_plan.get("responsibility"),
        "beneficiary_or_guardian": care_plan.get("beneficiaryOrGuardian"),
        "intervention_activities": care_plan.get("interventionActivities"),
        "assessment_field_code": care_plan.get("assessmentFieldCode"),
        "resources_funding": care_plan.get("resourcesFunding"),
        "risks_and_solutions": care_plan.get("risksAndSolutions"),
        "support_conditions": care_plan.get("supportConditions"),
        "plan_date": parse_iso_date(care_plan.get("planDate")),
        "start_date": parse_iso_date(care_plan.get("startDate")),
        "end_date": parse_iso_date(care_plan.get("endDate")),
        "approval_date": parse_iso_date(care_plan.get("approvalDate")),
        "review_date": parse_iso_date(care_plan.get("reviewDate")),
        "plan_number": care_plan.get("planNumber"),
        "implementing_units": join_values(implementing_units),
        "implementing_unit_count": len(implementing_units) if isinstance(implementing_units, list) else 0,
    }


def flatten_facility(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH facility record into a current-state staging row."""
    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "facility_id": record.get("id"),
        "facility_code": record.get("facilityCode"),
        "facility_name": record.get("facilityName"),
        "su_kien": record.get("suKien"),
        "is_active": record.get("active"),
        "phien_ban": record.get("phienBan"),
        "created_at": parse_epoch_millis(record.get("createdAt")) or parse_compact_timestamp(record.get("createdAtmm")),
        "updated_at": parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm")),
        "created_by": record.get("createdBy"),
        "updated_by": record.get("updatedBy"),
        "email": record.get("email"),
        "phone_number": record.get("phoneNumber"),
        "fax": record.get("fax"),
        "website": record.get("website"),
        "notes": record.get("notes"),
        "contact_address": record.get("contactAddress"),
        "ward_code": record.get("wardCode"),
        "province_id": record.get("provinceId"),
        "province_code": record.get("provinceCode"),
        "nationality": record.get("nationality"),
        "nationality_code": record.get("nationalityCode"),
        "area_type_code": record.get("areaTypeCode"),
        "center_type_id": record.get("centerTypeId"),
        "center_type_code": record.get("centerTypeCode"),
        "center_type_name": record.get("centerTypeName"),
        "facility_form": record.get("facilityForm"),
        "facility_form_name": record.get("facilityFormName"),
        "license_status": record.get("licenseStatus"),
        "management_unit_id": record.get("managementUnitId"),
        "management_unit_code": record.get("managementUnitCode"),
        "management_unit_name": record.get("managementUnitName"),
        "management_unit_type_id": record.get("managementUnitTypeId"),
        "director_name": record.get("directorName"),
        "director_birth_date": parse_iso_date(record.get("directorBirthDate")),
        "director_identity_number": record.get("directorIdentityNumber"),
        "director_document_type": record.get("directorDocumentType"),
        "director_document_type_code": record.get("directorDocumentTypeCode"),
        "decision_date": parse_iso_date(record.get("decisionDate")),
        "establishment_decision": record.get("establishmentDecision"),
        "establishment_year": record.get("establishmentYear"),
        "total_area": record.get("totalArea"),
        "total_staff": record.get("totalStaff"),
        "planned_capacity": record.get("plannedCapacity"),
        "total_beneficiaries": record.get("totalBeneficiaries"),
        "avg_area_per_beneficiary": record.get("avgAreaPerBeneficiary"),
        "avg_housing_area_per_beneficiary": record.get("avgHousingAreaPerBeneficiary"),
        "service_target_ids": join_values(record.get("serviceTargetIds")),
        "service_target_codes": join_values(record.get("serviceTargetCodes")),
    }


def flatten_social_worker(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH social-worker record into a current-state staging row."""
    residence = record.get("residenceInfo") or {}
    identity = record.get("personalIdentityDocument") or {}
    work_histories = record.get("workHistories") or []
    education_histories = record.get("educationHistories") or []
    practice_certifications = record.get("practiceCertifications") or []
    current_work = _pick_current_work_history(work_histories)

    gender_code = record.get("gender")
    try:
        gender_int = int(gender_code) if gender_code is not None else None
    except (TypeError, ValueError):
        gender_int = None

    gender_label = {1: "NAM", 2: "NU"}.get(gender_int, "KHONG_XAC_DINH")

    latest_education = None
    if isinstance(education_histories, list) and education_histories:
        latest_education = next((item for item in education_histories if isinstance(item, dict)), None)

    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "social_worker_id": record.get("id"),
        "su_kien": record.get("suKien"),
        "is_active": True,
        "phien_ban": record.get("phienBan"),
        "created_at": parse_epoch_millis(record.get("createdAt")) or parse_compact_timestamp(record.get("createdAtmm")),
        "updated_at": parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm")),
        "ho_va_ten": record.get("fullName"),
        "email": record.get("email"),
        "phone_number": record.get("phoneNumber"),
        "gioi_tinh_ma": gender_int,
        "gioi_tinh": gender_label,
        "ngay_sinh": parse_iso_date(record.get("dateOfBirth")),
        "ethnicity_id": record.get("ethnicityId"),
        "ethnicity_code": record.get("ethnicityCode"),
        "ethnicity_name": record.get("ethnicityName"),
        "nationality_id": record.get("nationalityId"),
        "nationality_code": record.get("nationalityCode"),
        "nationality_name": record.get("nationalityName"),
        "organization_id": record.get("organizationId"),
        "current_address": residence.get("currentAddress"),
        "current_ward_id": residence.get("currentWardId"),
        "current_ward_code": residence.get("currentWardCode"),
        "current_ward_name": residence.get("currentWardName"),
        "current_province_id": residence.get("currentProvinceId"),
        "current_province_code": residence.get("currentProvinceCode"),
        "current_province_name": residence.get("currentProvinceName"),
        "permanent_address": residence.get("newPermanentAddress") or residence.get("oldPermanentAddress"),
        "permanent_ward_id": residence.get("newPermanentWardId") or residence.get("oldPermanentWardId"),
        "permanent_ward_code": residence.get("newPermanentWardCode") or residence.get("oldWardCode"),
        "permanent_ward_name": residence.get("newPermanentWardName"),
        "permanent_province_id": residence.get("newPermanentProvinceId") or residence.get("oldPermanentProvinceId"),
        "permanent_province_code": residence.get("newPermanentProvinceCode") or residence.get("oldProvinceCode"),
        "permanent_province_name": residence.get("newPermanentProvinceName"),
        "document_number": identity.get("documentNumber"),
        "document_type_code": identity.get("documentTypeCode"),
        "document_type_name": identity.get("documentTypeName"),
        "document_issue_date": parse_iso_date(identity.get("issueDate")),
        "document_issue_place": identity.get("issuePlace"),
        "current_facility_id": current_work.get("facilityId"),
        "current_facility_code": current_work.get("facilityCode"),
        "current_facility_name": current_work.get("facilityName"),
        "current_facility_type": current_work.get("facilityType"),
        "current_position_code": current_work.get("positionCode"),
        "current_position_name": current_work.get("positionName"),
        "current_contract_type_code": current_work.get("contractTypeCode"),
        "current_contract_type_name": current_work.get("contractTypeName"),
        "current_job_description": current_work.get("jobDescription"),
        "current_work_start_date": parse_iso_date(current_work.get("startDate")),
        "current_work_end_date": parse_iso_date(current_work.get("endDate")),
        "education_level_code": latest_education.get("educationLevelCode") if isinstance(latest_education, dict) else None,
        "education_level_name": latest_education.get("educationLevelName") if isinstance(latest_education, dict) else None,
        "major_code": latest_education.get("majorCode") if isinstance(latest_education, dict) else None,
        "major_name": latest_education.get("majorName") if isinstance(latest_education, dict) else None,
        "graduation_year": latest_education.get("graduationYear") if isinstance(latest_education, dict) else None,
        "work_history_count": len(work_histories) if isinstance(work_histories, list) else 0,
        "education_history_count": len(education_histories) if isinstance(education_histories, list) else 0,
        "practice_certification_count": len(practice_certifications) if isinstance(practice_certifications, list) else 0,
    }


def explode_social_worker_work_histories(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode social worker work histories into one row per work history item."""
    work_histories = record.get("workHistories") or []
    if not isinstance(work_histories, list) or not work_histories:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    social_worker_id = record.get("id")

    rows: list[dict[str, t.Any]] = []
    for history in work_histories:
        if not isinstance(history, dict):
            continue

        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "social_worker_id": social_worker_id,
                "updated_at": updated_at,
                "work_history_id": history.get("id"),
                "is_current": history.get("isCurrent"),
                "status": history.get("status"),
                "start_date": parse_iso_date(history.get("startDate")),
                "end_date": parse_iso_date(history.get("endDate")),
                "facility_id": history.get("facilityId"),
                "facility_code": history.get("facilityCode"),
                "facility_name": history.get("facilityName"),
                "facility_type": history.get("facilityType"),
                "position_id": history.get("positionId"),
                "position_code": history.get("positionCode"),
                "position_name": history.get("positionName"),
                "contract_type_id": history.get("contractTypeId"),
                "contract_type_code": history.get("contractTypeCode"),
                "contract_type_name": history.get("contractTypeName"),
                "job_description": history.get("jobDescription"),
            }
        )

    return rows


def flatten_work_history_record(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH WorkHistories record into one staging row."""
    work_history = record.get("workHistory") or {}
    social_worker = record.get("socialWorker") or {}

    gender_code = social_worker.get("gender")
    try:
        gender_int = int(gender_code) if gender_code is not None else None
    except (TypeError, ValueError):
        gender_int = None

    gender_label = {1: "NAM", 2: "NU"}.get(gender_int, "KHONG_XAC_DINH")

    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "work_history_id": record.get("id"),
        "su_kien": record.get("suKien"),
        "phien_ban": record.get("phienBan"),
        "created_at": parse_epoch_millis(record.get("createdAt")) or parse_compact_timestamp(record.get("createdAtmm")),
        "updated_at": parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm")),
        "social_worker_id": social_worker.get("id"),
        "ho_va_ten": social_worker.get("fullName"),
        "email": social_worker.get("email"),
        "phone_number": social_worker.get("phoneNumber"),
        "gioi_tinh_ma": gender_int,
        "gioi_tinh": gender_label,
        "ngay_sinh": parse_iso_date(social_worker.get("dateOfBirth")),
        "ethnicity_code": social_worker.get("ethnicityCode"),
        "ethnicity_name": social_worker.get("ethnicityName"),
        "nationality_code": social_worker.get("nationalityCode"),
        "nationality_name": social_worker.get("nationalityName"),
        "organization_id": social_worker.get("organizationId"),
        "document_number": social_worker.get("documentNumber"),
        "document_type_code": social_worker.get("documentTypeCode"),
        "document_type_name": social_worker.get("documentTypeName"),
        "document_issue_date": parse_iso_date(social_worker.get("issueDate")),
        "document_issue_place": social_worker.get("issuePlace"),
        "current_address": social_worker.get("currentAddress"),
        "current_ward_id": social_worker.get("currentWardId"),
        "current_ward_code": social_worker.get("currentWardCode"),
        "current_ward_name": social_worker.get("currentWardName"),
        "current_province_id": social_worker.get("currentProvinceId"),
        "current_province_code": social_worker.get("currentProvinceCode"),
        "current_province_name": social_worker.get("currentProvinceName"),
        "permanent_address": social_worker.get("newPermanentAddress") or social_worker.get("oldPermanentAddress"),
        "permanent_ward_id": social_worker.get("newPermanentWardId") or social_worker.get("oldPermanentWardId"),
        "permanent_ward_code": social_worker.get("newPermanentWardCode"),
        "permanent_ward_name": social_worker.get("newPermanentWardName"),
        "permanent_province_id": social_worker.get("newPermanentProvinceId") or social_worker.get("oldPermanentProvinceId"),
        "permanent_province_code": social_worker.get("newPermanentProvinceCode") or social_worker.get("oldProvinceCode"),
        "permanent_province_name": social_worker.get("newPermanentProvinceName"),
        "status": work_history.get("status"),
        "is_current": work_history.get("isCurrent"),
        "start_date": parse_iso_date(work_history.get("startDate")),
        "end_date": parse_iso_date(work_history.get("endDate")),
        "facility_id": work_history.get("facilityId"),
        "facility_code": work_history.get("facilityCode"),
        "facility_name": work_history.get("facilityName"),
        "facility_type": work_history.get("facilityType"),
        "position_id": work_history.get("positionId"),
        "position_code": work_history.get("positionCode"),
        "position_name": work_history.get("positionName"),
        "contract_type_id": work_history.get("contractTypeId"),
        "contract_type_code": work_history.get("contractTypeCode"),
        "contract_type_name": work_history.get("contractTypeName"),
        "job_description": work_history.get("jobDescription"),
    }