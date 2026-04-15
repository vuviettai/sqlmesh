"""Parsing helpers for BTXH staging sources."""
from __future__ import annotations

import typing as t
from itertools import zip_longest

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


def _pick_first_non_empty(*values: t.Any) -> t.Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _ensure_list(value: t.Any) -> list[t.Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [value]


def _as_text(value: t.Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        return join_values(value)
    if isinstance(value, dict):
        non_empty_values = [item for item in value.values() if item not in (None, "")]
        return join_values(non_empty_values)
    return str(value)


def _extract_center_profiles(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    center_profiles = record.get("centerProfiles") or record.get("centerProfile") or []
    if not isinstance(center_profiles, list):
        center_profiles = [center_profiles] if center_profiles else []
    return [profile for profile in center_profiles if isinstance(profile, dict)]


def flatten_beneficiary(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH beneficiary record into a current-state staging row."""
    residence = record.get("residence") or {}
    paper_identity = record.get("paperIdentity") or {}
    center_profiles = _extract_center_profiles(record)
    primary_profile = pick_primary_center_profile(center_profiles)

    gender_code = record.get("gender")
    try:
        gender_int = int(gender_code) if gender_code is not None else None
    except (TypeError, ValueError):
        gender_int = None

    gender_label = {1: "NAM", 2: "NU"}.get(gender_int, "KHONG_XAC_DINH")

    # Safely extract services from primary profile
    services = primary_profile.get("services")
    service_codes = None
    if isinstance(services, str):
        service_codes = services.split(",")
    elif isinstance(services, list):
        service_codes = services
    
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
        "danh_sach_ma_dich_vu": join_values(service_codes),
        "danh_sach_dich_vu": join_values(primary_profile.get("providedServices")),
    }


def explode_beneficiary_center_profiles(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH center profiles into one row per beneficiary profile."""
    center_profiles = _extract_center_profiles(record)
    if not center_profiles:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))

    rows: list[dict[str, t.Any]] = []
    for profile in center_profiles:
        if not isinstance(profile, dict):
            continue

        # Safely handle services field - could be string, list, or missing
        services = profile.get("services")
        if isinstance(services, str):
            service_codes = services.split(",")
        elif isinstance(services, list):
            service_codes = services
        else:
            service_codes = None

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


def explode_center_profile_family_info(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode centerProfiles[].familyInfo into one row per center profile with family info."""
    center_profiles = _extract_center_profiles(record)
    if not center_profiles:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    beneficiary_id = record.get("id")
    rows: list[dict[str, t.Any]] = []

    for profile in center_profiles:
        family_info = profile.get("familyInfo") or {}
        if not isinstance(family_info, dict) or not family_info:
            continue
        guardian = family_info.get("guardian") or {}
        household_head = family_info.get("householdHead") or {}
        policy_benefits = _ensure_list(family_info.get("policyBenefits"))
        poverty_decisions = _ensure_list(family_info.get("povertyDecisions"))

        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "beneficiary_id": beneficiary_id,
                "center_profile_id": profile.get("id"),
                "facility_id": profile.get("facilityId"),
                "facility_code": profile.get("facilityCode"),
                "updated_at": updated_at,
                "family_info_id": family_info.get("id"),
                "guardian_id": guardian.get("id"),
                "guardian_full_name": guardian.get("fullName"),
                "guardian_gender": guardian.get("gender"),
                "guardian_phone": guardian.get("phone"),
                "guardian_relationship_code": guardian.get("relationshipCode"),
                "guardian_ward_code": guardian.get("wardCode"),
                "guardian_province_code": guardian.get("provinceCode"),
                "household_head_full_name": household_head.get("fullName"),
                "household_head_gender": household_head.get("gender"),
                "household_head_phone": household_head.get("phone"),
                "household_head_relationship_code": household_head.get("relationshipCode"),
                "income_cash": family_info.get("incomeCash"),
                "income_kind": family_info.get("incomeKind"),
                "other_social_assistance": family_info.get("otherSocialAssistance"),
                "total_family_members": family_info.get("totalFamilyMembers"),
                "total_main_working_members": family_info.get("totalMainWorkingMembers"),
                "policy_benefit_count": len(policy_benefits),
                "poverty_decision_count": len(poverty_decisions),
            }
        )

    return rows


def explode_center_profile_medical_info(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode centerProfiles[].medicalInfo into one row per center profile with medical info."""
    center_profiles = _extract_center_profiles(record)
    if not center_profiles:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    beneficiary_id = record.get("id")
    rows: list[dict[str, t.Any]] = []

    for profile in center_profiles:
        medical_info = profile.get("medicalInfo") or {}
        if not isinstance(medical_info, dict) or not medical_info:
            continue

        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "beneficiary_id": beneficiary_id,
                "center_profile_id": profile.get("id"),
                "facility_id": profile.get("facilityId"),
                "facility_code": profile.get("facilityCode"),
                "updated_at": updated_at,
                "medical_person_id": _as_text(medical_info.get("personId")),
                "labor_capacity": _as_text(medical_info.get("laborCapacity")),
                "medical_record": _as_text(medical_info.get("medicalRecord")),
                "disability_type_code": _as_text(medical_info.get("disabilityTypeCode")),
                "disability_cause_code": _as_text(medical_info.get("disabilityCauseCode")),
                "disability_level_code": _as_text(medical_info.get("disabilityLevelCode")),
                "self_service_ability_code": _as_text(medical_info.get("selfServiceAbilityCode")),
                "physical_mental_status": _as_text(medical_info.get("physicalMentalStatus")),
                "disability_characteristics": _as_text(medical_info.get("disabilityCharacteristics")),
                "other_disability_cause": _as_text(medical_info.get("otherDisabilityCause")),
            }
        )

    return rows


def explode_facility_service_targets(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH facility service targets into one row per target mapping."""
    target_ids = _ensure_list(record.get("serviceTargetIds"))
    target_codes = _ensure_list(record.get("serviceTargetCodes"))
    if not target_ids and not target_codes:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    rows: list[dict[str, t.Any]] = []
    for target_id, target_code in zip_longest(target_ids, target_codes, fillvalue=None):
        normalized_target_id = None if target_id in (None, "") else str(target_id)
        normalized_target_code = None if target_code in (None, "") else str(target_code)
        if normalized_target_id is None and normalized_target_code is None:
            continue

        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "facility_id": record.get("id"),
                "facility_code": record.get("facilityCode"),
                "facility_name": record.get("facilityName"),
                "updated_at": updated_at,
                "center_type_code": record.get("centerTypeCode"),
                "service_target_id": normalized_target_id,
                "service_target_code": normalized_target_code,
            }
        )

    return rows


def explode_beneficiary_attachments(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH beneficiary attachments into one row per attachment."""
    attachments = record.get("attachments") or []
    if not isinstance(attachments, list) or not attachments:
        return []

    rows: list[dict[str, t.Any]] = []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "beneficiary_id": record.get("id"),
                "updated_at": parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm")),
                "attachment_id": attachment.get("id"),
                "file_id": attachment.get("fileId"),
                "file_name": attachment.get("fileName"),
                "created_at": attachment.get("createdAt"),
                "attachment_updated_at": attachment.get("updatedAt"),
                "description": attachment.get("description"),
                "attachment_type": attachment.get("attachmentType"),
            }
        )

    return rows


def explode_social_worker_documents(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH social worker documents into one row per document."""
    documents = record.get("documents") or []
    if not isinstance(documents, list) or not documents:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    rows: list[dict[str, t.Any]] = []
    for document in documents:
        if not isinstance(document, dict):
            continue
        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "social_worker_id": record.get("id"),
                "updated_at": updated_at,
                "document_id": document.get("id"),
                "file_id": document.get("fileId"),
                "file_name": document.get("fileName"),
                "document_type": document.get("documentType"),
                "original_file_name": document.get("originalFileName"),
            }
        )

    return rows


def explode_social_worker_education_histories(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH social worker education histories into one row per education item."""
    education_histories = record.get("educationHistories") or []
    if not isinstance(education_histories, list) or not education_histories:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    rows: list[dict[str, t.Any]] = []
    for education in education_histories:
        if not isinstance(education, dict):
            continue
        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "social_worker_id": record.get("id"),
                "updated_at": updated_at,
                "education_history_id": education.get("id"),
                "education_level_code": education.get("educationLevelCode"),
                "education_level_name": education.get("educationLevelName"),
                "major_code": education.get("majorCode"),
                "major_name": education.get("majorName"),
                "graduation_year": education.get("graduationYear"),
                "institution_name": education.get("institutionName"),
            }
        )

    return rows


def explode_social_worker_practice_certifications(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH social worker practice certifications into one row per certification."""
    certifications = record.get("practiceCertifications") or []
    if not isinstance(certifications, list) or not certifications:
        return []

    updated_at = parse_epoch_millis(record.get("updatedAt")) or parse_compact_timestamp(record.get("updatedAtmm"))
    rows: list[dict[str, t.Any]] = []
    for certification in certifications:
        if not isinstance(certification, dict):
            continue
        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "social_worker_id": record.get("id"),
                "updated_at": updated_at,
                "practice_certification_id": certification.get("id"),
                "certificate_number": certification.get("certificateNumber"),
                "certificate_name": certification.get("certificateName"),
                "issued_by": certification.get("issuedBy"),
                "issued_date": parse_iso_date(certification.get("issuedDate")),
                "expiry_date": parse_iso_date(certification.get("expiryDate")),
                "status": certification.get("status"),
            }
        )

    return rows


def flatten_care_activity(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH care activity record into one row per care plan activity."""
    person = record.get("person") or {}
    care_plan = record.get("carePlan") or {}
    beneficiary = care_plan.get("beneficiary") or person or {}
    social_worker = care_plan.get("socialWorker") or record.get("socialWorker") or {}
    center_profiles = (
        beneficiary.get("centerProfiles")
        or beneficiary.get("centerProfile")
        or care_plan.get("centerProfiles")
        or care_plan.get("centerProfile")
        or []
    )
    if not isinstance(center_profiles, list):
        center_profiles = [center_profiles] if center_profiles else []
    primary_profile = pick_primary_center_profile(center_profiles)

    beneficiary_gender_code = _pick_first_non_empty(
        beneficiary.get("gender"),
        care_plan.get("beneficiaryGender"),
    )
    social_worker_gender_code = social_worker.get("gender")
    try:
        beneficiary_gender_int = int(beneficiary_gender_code) if beneficiary_gender_code is not None else None
    except (TypeError, ValueError):
        beneficiary_gender_int = None
    try:
        social_worker_gender_int = int(social_worker_gender_code) if social_worker_gender_code is not None else None
    except (TypeError, ValueError):
        social_worker_gender_int = None

    beneficiary_gender_label = {1: "NAM", 2: "NU"}.get(beneficiary_gender_int, "KHONG_XAC_DINH")
    social_worker_gender_label = {1: "NAM", 2: "NU"}.get(social_worker_gender_int, "KHONG_XAC_DINH")
    implementing_units = care_plan.get("implementingUnits")

    return {
        "_airbyte_raw_id": record.get("_airbyte_raw_id"),
        "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
        "_airbyte_generation_id": record.get("_airbyte_generation_id"),
        "care_activity_id": record.get("id"),
        "social_worker_id": _pick_first_non_empty(social_worker.get("personId"), social_worker.get("id")),
        "beneficiary_id": _pick_first_non_empty(
            care_plan.get("beneficiaryId"),
            beneficiary.get("id"),
        ),
        "su_kien": record.get("suKien"),
        "phien_ban": record.get("phienBan"),
        "created_at": parse_compact_timestamp(record.get("createdAtmm")),
        "updated_at": parse_compact_timestamp(record.get("updatedAtmm")),
        "beneficiary_ho_va_ten": _pick_first_non_empty(
            beneficiary.get("fullName"),
            care_plan.get("beneficiaryName"),
        ),
        "beneficiary_gioi_tinh_ma": beneficiary_gender_int,
        "beneficiary_gioi_tinh": beneficiary_gender_label,
        "beneficiary_ngay_sinh": parse_iso_date(
            _pick_first_non_empty(
                beneficiary.get("dateOfBirth"),
                care_plan.get("beneficiaryDateOfBirth"),
            )
        ),
        "beneficiary_quoc_tich": _pick_first_non_empty(
            beneficiary.get("nationality"),
            care_plan.get("beneficiaryNationality"),
        ),
        "social_worker_ho_va_ten": social_worker.get("fullName"),
        "social_worker_gioi_tinh_ma": social_worker_gender_int,
        "social_worker_gioi_tinh": social_worker_gender_label,
        "social_worker_ngay_sinh": parse_iso_date(social_worker.get("dateOfBirth")),
        "social_worker_quoc_tich": social_worker.get("nationality"),
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


def explode_care_plans(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH care plans into one row per care plan."""
    person = record.get("person") or {}
    care_plan = record.get("carePlan") or {}
    if not isinstance(care_plan, dict) or not care_plan.get("id"):
        return []

    beneficiary = care_plan.get("beneficiary") or person or {}
    center_profiles = (
        beneficiary.get("centerProfiles")
        or beneficiary.get("centerProfile")
        or care_plan.get("centerProfiles")
        or care_plan.get("centerProfile")
        or []
    )
    if not isinstance(center_profiles, list):
        center_profiles = [center_profiles] if center_profiles else []
    primary_profile = pick_primary_center_profile(center_profiles)

    updated_at = parse_compact_timestamp(record.get("updatedAtmm")) or parse_compact_timestamp(record.get("createdAtmm"))
    implementing_units = _ensure_list(care_plan.get("implementingUnits"))

    return [
        {
            "_airbyte_raw_id": record.get("_airbyte_raw_id"),
            "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
            "_airbyte_generation_id": record.get("_airbyte_generation_id"),
            "care_activity_id": record.get("id"),
            "beneficiary_id": _pick_first_non_empty(care_plan.get("beneficiaryId"), beneficiary.get("id")),
            "center_profile_id": primary_profile.get("id"),
            "facility_id": primary_profile.get("facilityId"),
            "facility_code": primary_profile.get("facilityCode"),
            "updated_at": updated_at,
            "care_plan_id": care_plan.get("id"),
            "care_plan_status": care_plan.get("status"),
            "plan_date": parse_iso_date(care_plan.get("planDate")),
            "start_date": parse_iso_date(care_plan.get("startDate")),
            "end_date": parse_iso_date(care_plan.get("endDate")),
            "approval_date": parse_iso_date(care_plan.get("approvalDate")),
            "review_date": parse_iso_date(care_plan.get("reviewDate")),
            "plan_number": care_plan.get("planNumber"),
            "object_manager": care_plan.get("objectManager"),
            "beneficiary_or_guardian": care_plan.get("beneficiaryOrGuardian"),
            "facility_head_or_chairman": care_plan.get("facilityHeadOrChairman"),
            "implementing_units": join_values(implementing_units),
            "implementing_unit_count": len(implementing_units),
        }
    ]


def explode_care_plan_objectives(record: dict[str, t.Any]) -> list[dict[str, t.Any]]:
    """Explode BTXH care plan objectives into one row per objective."""
    person = record.get("person") or {}
    care_plan = record.get("carePlan") or {}
    if not isinstance(care_plan, dict) or not care_plan.get("id"):
        return []

    objectives = care_plan.get("objectives") or []
    if not isinstance(objectives, list) or not objectives:
        return []

    beneficiary = care_plan.get("beneficiary") or person or {}
    center_profiles = (
        beneficiary.get("centerProfiles")
        or beneficiary.get("centerProfile")
        or care_plan.get("centerProfiles")
        or care_plan.get("centerProfile")
        or []
    )
    if not isinstance(center_profiles, list):
        center_profiles = [center_profiles] if center_profiles else []
    primary_profile = pick_primary_center_profile(center_profiles)

    updated_at = parse_compact_timestamp(record.get("updatedAtmm")) or parse_compact_timestamp(record.get("createdAtmm"))
    rows: list[dict[str, t.Any]] = []
    for objective in objectives:
        if not isinstance(objective, dict):
            continue
        rows.append(
            {
                "_airbyte_raw_id": record.get("_airbyte_raw_id"),
                "_airbyte_extracted_at": record.get("_airbyte_extracted_at"),
                "_airbyte_generation_id": record.get("_airbyte_generation_id"),
                "care_activity_id": record.get("id"),
                "care_plan_id": care_plan.get("id"),
                "objective_id": objective.get("id"),
                "beneficiary_id": _pick_first_non_empty(care_plan.get("beneficiaryId"), beneficiary.get("id")),
                "center_profile_id": primary_profile.get("id"),
                "facility_id": primary_profile.get("facilityId"),
                "facility_code": primary_profile.get("facilityCode"),
                "updated_at": updated_at,
                "plan_date": parse_iso_date(care_plan.get("planDate")),
                "approval_date": parse_iso_date(care_plan.get("approvalDate")),
                "review_date": parse_iso_date(care_plan.get("reviewDate")),
                "objective_code": objective.get("code"),
                "specific_goal": objective.get("specificGoal"),
                "priority_level": objective.get("priorityLevel"),
                "assessment_field_code": objective.get("assessmentFieldCode"),
            }
        )

    return rows


def flatten_facility(record: dict[str, t.Any]) -> dict[str, t.Any]:
    """Flatten a BTXH facility record into a current-state staging row."""
    # Safely handle serviceTargetIds and serviceTargetCodes - could be string, list, dict, or missing
    service_target_ids = record.get("serviceTargetIds")
    if isinstance(service_target_ids, str):
        service_target_ids_parsed = service_target_ids.split(",") if service_target_ids else None
    elif isinstance(service_target_ids, list):
        service_target_ids_parsed = service_target_ids
    elif isinstance(service_target_ids, dict):
        service_target_ids_parsed = list(service_target_ids.values()) if service_target_ids else None
    else:
        service_target_ids_parsed = None

    service_target_codes = record.get("serviceTargetCodes")
    if isinstance(service_target_codes, str):
        service_target_codes_parsed = service_target_codes.split(",") if service_target_codes else None
    elif isinstance(service_target_codes, list):
        service_target_codes_parsed = service_target_codes
    elif isinstance(service_target_codes, dict):
        service_target_codes_parsed = list(service_target_codes.values()) if service_target_codes else None
    else:
        service_target_codes_parsed = None

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
        "service_target_ids": join_values(service_target_ids_parsed),
        "service_target_codes": join_values(service_target_codes_parsed),
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
        "social_worker_id": _pick_first_non_empty(
            work_history.get("socialWorkerId"),
            social_worker.get("socialWorkerId"),
            social_worker.get("id"),
        ),
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