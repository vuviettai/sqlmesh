/* =============================================================================
  sqlmesh_work.src_btxh_fact_hoat_dong_cham_soc
   ============================================
   Fact: hoạt động / kế hoạch chăm sóc BTXH.
   Grain: CARE_ACTIVITY_ID – một dòng per care activity.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_fact_hoat_dong_cham_soc,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_hoat_dong_cham_soc
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_hoat_dong_cham_soc,
  tags        (fact, btxh, care_activity),
  description 'BTXH care activity fact – one row per care activity / care plan record.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY care_activity_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_care_activities
  WHERE care_activity_id IS NOT NULL
    AND beneficiary_id IS NOT NULL
)

SELECT
  care_activity_id::VARCHAR(64)                                     AS ma_hoat_dong_cham_soc,
  beneficiary_id::VARCHAR(64)                                       AS ma_nguoi_thu_huong,
  ma_co_so::VARCHAR(30)                                             AS ma_co_so,
  care_plan_id::VARCHAR(64)                                         AS ma_ke_hoach_cham_soc,
  COALESCE(care_plan_status, 'KHONG_XAC_DINH')::VARCHAR(50)         AS trang_thai_ke_hoach_cham_soc,
  goal_code::VARCHAR(50)                                            AS ma_muc_tieu,
  goal_description::TEXT                                            AS mo_ta_muc_tieu,
  priority_level::VARCHAR(50)                                       AS muc_do_uu_tien,
  manager_name::VARCHAR(255)                                        AS ten_nguoi_quan_ly,
  facility_leader_name::VARCHAR(255)                                AS ten_lanh_dao_co_so,
  responsibility::TEXT                                              AS trach_nhiem,
  beneficiary_or_guardian::TEXT                                     AS doi_tuong_hoac_nguoi_giam_ho,
  intervention_activities::TEXT                                     AS hoat_dong_can_thiep,
  assessment_field_code::VARCHAR(50)                                AS ma_linh_vuc_danh_gia,
  resources_funding::TEXT                                           AS nguon_luc_kinh_phi,
  risks_and_solutions::TEXT                                         AS rui_ro_va_giai_phap,
  support_conditions::TEXT                                          AS dieu_kien_ho_tro,
  plan_date::DATE                                                   AS ngay_lap_ke_hoach,
  start_date::DATE                                                  AS ngay_bat_dau,
  end_date::DATE                                                    AS ngay_ket_thuc,
  approval_date::DATE                                               AS ngay_phe_duyet,
  review_date::DATE                                                 AS ngay_ra_soat,
  plan_number::VARCHAR(100)                                         AS so_ke_hoach,
  implementing_units::TEXT                                          AS danh_sach_don_vi_thuc_hien,
  COALESCE(implementing_unit_count, 0)::INT                         AS so_don_vi_thuc_hien,
  updated_at::DATE                                                  AS ngay_cap_nhat
FROM latest
WHERE rn = 1