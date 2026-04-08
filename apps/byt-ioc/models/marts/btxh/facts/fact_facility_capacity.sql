/* =============================================================================
  sqlmesh_work.src_btxh_fact_nang_luc_co_so
   ========================================
   Fact: snapshot năng lực và quy mô vận hành của cơ sở BTXH.
   Grain: (MA_CO_SO, NGAY_CAP_NHAT) – một dòng per facility snapshot per day.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_fact_nang_luc_co_so,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  (ma_co_so, ngay_cap_nhat)
  ),
  owner       data_team,
  cron        '@daily',
  grain       (ma_co_so, ngay_cap_nhat),
  tags        (fact, btxh, facility_capacity),
  description 'BTXH facility capacity fact – daily facility capacity, staffing, and occupancy snapshot.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY facility_code, updated_at::DATE
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_facilities
  WHERE facility_code IS NOT NULL
    AND updated_at IS NOT NULL
)

SELECT
  facility_code::VARCHAR(30)                                                              AS ma_co_so,
  facility_id::VARCHAR(64)                                                                AS ma_dinh_danh_nguon_co_so,
  center_type_code::VARCHAR(50)                                                           AS ma_loai_trung_tam,
  facility_form::VARCHAR(50)                                                              AS ma_hinh_thuc_co_so,
  NULLIF(REGEXP_REPLACE(planned_capacity, '[^0-9.-]', '', 'g'), '')::INT                  AS cong_suat_ke_hoach,
  NULLIF(REGEXP_REPLACE(total_staff, '[^0-9.-]', '', 'g'), '')::INT                       AS tong_nhan_su,
  NULLIF(REGEXP_REPLACE(total_beneficiaries, '[^0-9.-]', '', 'g'), '')::INT               AS tong_doi_tuong,
  NULLIF(REGEXP_REPLACE(total_area, '[^0-9.-]', '', 'g'), '')::DECIMAL(18, 2)            AS tong_dien_tich,
  NULLIF(REGEXP_REPLACE(avg_area_per_beneficiary, '[^0-9.-]', '', 'g'), '')::DECIMAL(18, 2)
                                                                                           AS dien_tich_binh_quan_mot_doi_tuong,
  NULLIF(REGEXP_REPLACE(avg_housing_area_per_beneficiary, '[^0-9.-]', '', 'g'), '')::DECIMAL(18, 2)
                                                                                           AS dien_tich_nha_o_binh_quan_mot_doi_tuong,
  COALESCE(is_active, TRUE)::BOOLEAN                                                      AS dang_hoat_dong,
  updated_at::DATE                                                                         AS ngay_cap_nhat
FROM latest
WHERE rn = 1