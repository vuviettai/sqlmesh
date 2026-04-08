/* =============================================================================
  sqlmesh_work.src_btxh_dim_nhan_vien_ctxh
   =======================================
   Dimension: nhân viên công tác xã hội BTXH.
   Grain: MA_NHAN_VIEN_CTXH – một dòng per social worker (bản cập nhật mới nhất).
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_dim_nhan_vien_ctxh,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_nhan_vien_ctxh
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_nhan_vien_ctxh,
  tags        (dimension, btxh, social_worker),
  description 'BTXH social worker dimension – latest demographics, identity, and current employment context.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY social_worker_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_social_workers
  WHERE social_worker_id IS NOT NULL
)

SELECT
  social_worker_id::VARCHAR(64)                                     AS ma_nhan_vien_ctxh,
  ho_va_ten::VARCHAR(255)                                           AS ho_va_ten,
  gioi_tinh::VARCHAR(50)                                            AS gioi_tinh,
  ngay_sinh::DATE                                                   AS ngay_sinh,
  ethnicity_code::VARCHAR(20)                                       AS ma_dan_toc,
  ethnicity_name::VARCHAR(100)                                      AS ten_dan_toc,
  nationality_code::VARCHAR(20)                                     AS ma_quoc_tich,
  nationality_name::VARCHAR(100)                                    AS ten_quoc_tich,
  phone_number::VARCHAR(50)                                         AS so_dien_thoai,
  email::VARCHAR(255)                                               AS thu_dien_tu,
  current_province_code::VARCHAR(10)                                AS ma_tinh,
  current_address::TEXT                                             AS dia_chi,
  document_number::VARCHAR(50)                                      AS so_giay_to,
  document_type_code::VARCHAR(20)                                   AS ma_loai_giay_to,
  document_type_name::VARCHAR(100)                                  AS ten_loai_giay_to,
  document_issue_date::DATE                                         AS ngay_cap_giay_to,
  document_issue_place::VARCHAR(255)                                AS noi_cap_giay_to,
  organization_id::VARCHAR(64)                                      AS ma_to_chuc,
  current_facility_code::VARCHAR(30)                                AS ma_co_so_hien_tai,
  current_facility_name::VARCHAR(255)                               AS ten_co_so_hien_tai,
  current_facility_type::VARCHAR(50)                                AS loai_co_so_hien_tai,
  current_position_code::VARCHAR(50)                                AS ma_vi_tri_hien_tai,
  current_position_name::VARCHAR(255)                               AS ten_vi_tri_hien_tai,
  current_contract_type_code::VARCHAR(50)                           AS ma_loai_hop_dong_hien_tai,
  current_contract_type_name::VARCHAR(255)                          AS ten_loai_hop_dong_hien_tai,
  education_level_code::VARCHAR(50)                                 AS ma_trinh_do_hoc_van,
  education_level_name::VARCHAR(255)                                AS ten_trinh_do_hoc_van,
  major_code::VARCHAR(50)                                           AS ma_chuyen_nganh,
  major_name::VARCHAR(255)                                          AS ten_chuyen_nganh,
  graduation_year::VARCHAR(10)                                      AS nam_tot_nghiep,
  COALESCE(work_history_count, 0)::INT                              AS so_lich_su_cong_tac,
  COALESCE(education_history_count, 0)::INT                         AS so_lich_su_hoc_van,
  COALESCE(practice_certification_count, 0)::INT                    AS so_chung_chi_hanh_nghe,
  TRUE::BOOLEAN                                                     AS dang_hoat_dong,
  updated_at::DATE                                                  AS ngay_cap_nhat
FROM latest
WHERE rn = 1