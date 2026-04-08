/* =============================================================================
  sqlmesh_work.src_btxh_fact_gan_dich_vu
   =====================================
   Fact: dịch vụ được gán cho hồ sơ trung tâm BTXH.
   Grain: (CENTER_PROFILE_ID, MA_DICH_VU) – một dòng per hồ sơ per dịch vụ.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_fact_gan_dich_vu,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  [ma_ho_so_trung_tam, ma_dich_vu]
  ),
  owner       data_team,
  cron        '@daily',
  grain       [ma_ho_so_trung_tam, ma_dich_vu],
  tags        (fact, btxh, service_assignment),
  description 'BTXH service assignment fact – one row per center profile and service code.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY center_profile_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_center_profiles
  WHERE center_profile_id IS NOT NULL
    AND beneficiary_id IS NOT NULL
    AND ma_co_so IS NOT NULL
    AND NULLIF(ma_dich_vu, '') IS NOT NULL
),

service_codes AS (
  SELECT
    l.center_profile_id,
    l.beneficiary_id,
    l.ma_co_so,
    l.ngay_tiep_nhan,
    l.ngay_quyet_dinh_tiep_nhan,
    l.ma_trang_thai_ho_so,
    l.loai_luu_tru,
    l.profile_active,
    l.profile_deleted,
    l.updated_at,
    code.ordinality,
    NULLIF(BTRIM(code.service_code), '') AS ma_dich_vu
  FROM latest l
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(l.ma_dich_vu, ',')) WITH ORDINALITY AS code(service_code, ordinality)
  WHERE l.rn = 1
),

service_names AS (
  SELECT
    l.center_profile_id,
    name.ordinality,
    NULLIF(BTRIM(name.service_name), '') AS ten_dich_vu
  FROM latest l
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(COALESCE(l.ten_dich_vu, ''), ',')) WITH ORDINALITY AS name(service_name, ordinality)
  WHERE l.rn = 1
)

SELECT
  s.center_profile_id::VARCHAR(64)                                   AS ma_ho_so_trung_tam,
  s.beneficiary_id::VARCHAR(64)                                      AS ma_nguoi_thu_huong,
  s.ma_co_so::VARCHAR(30)                                            AS ma_co_so,
  s.ma_dich_vu::VARCHAR(50)                                          AS ma_dich_vu,
  COALESCE(n.ten_dich_vu, 'KHONG_XAC_DINH')::VARCHAR(255)            AS ten_dich_vu,
  s.ngay_tiep_nhan::DATE                                             AS ngay_tiep_nhan,
  s.ngay_quyet_dinh_tiep_nhan::DATE                                  AS ngay_quyet_dinh_tiep_nhan,
  COALESCE(s.ma_trang_thai_ho_so, 'KHONG_XAC_DINH')::VARCHAR(50)     AS trang_thai_ho_so,
  s.loai_luu_tru::VARCHAR(100)                                       AS loai_luu_tru,
  COALESCE(s.profile_active, FALSE)::BOOLEAN                         AS ho_so_dang_hoat_dong,
  COALESCE(s.profile_deleted, FALSE)::BOOLEAN                        AS ho_so_da_xoa,
  s.updated_at::DATE                                                 AS ngay_cap_nhat

FROM service_codes s
LEFT JOIN service_names n
  ON n.center_profile_id = s.center_profile_id
 AND n.ordinality = s.ordinality
WHERE s.ma_dich_vu IS NOT NULL