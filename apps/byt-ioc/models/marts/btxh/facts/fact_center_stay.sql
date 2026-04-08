/* =============================================================================
  sqlmesh_work.src_btxh_fact_ho_so_trung_tam
   =========================================
   Fact: đợt lưu trú / hồ sơ trung tâm BTXH.
   Grain: CENTER_PROFILE_ID – một dòng per hồ sơ trung tâm.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_fact_ho_so_trung_tam,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_ho_so_trung_tam
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_ho_so_trung_tam,
  tags        (fact, btxh, center_stay),
  description 'BTXH center stay fact – one row per beneficiary center profile.'
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
)

SELECT
  center_profile_id::VARCHAR(64)                                     AS ma_ho_so_trung_tam,
  beneficiary_id::VARCHAR(64)                                        AS ma_nguoi_thu_huong,
  ma_co_so::VARCHAR(30)                                              AS ma_co_so,
  ngay_tiep_nhan::DATE                                               AS ngay_tiep_nhan,
  ngay_quyet_dinh_tiep_nhan::DATE                                    AS ngay_quyet_dinh_tiep_nhan,
  so_quyet_dinh_tiep_nhan::VARCHAR(100)                              AS so_quyet_dinh_tiep_nhan,
  co_so_ban_hanh_quyet_dinh::VARCHAR(255)                            AS co_so_ban_hanh_quyet_dinh,
  so_quyet_dinh::VARCHAR(100)                                        AS so_quyet_dinh,
  COALESCE(ma_trang_thai_ho_so, 'KHONG_XAC_DINH')::VARCHAR(50)      AS trang_thai_ho_so,
  loai_luu_tru::VARCHAR(100)                                         AS loai_luu_tru,
  ma_nhom_doi_tuong_chinh::VARCHAR(50)                               AS ma_nhom_doi_tuong_chinh,
  ma_nhom_doi_tuong::TEXT                                            AS danh_sach_ma_nhom_doi_tuong,
  ma_chi_tiet_doi_tuong::TEXT                                        AS danh_sach_ma_chi_tiet_doi_tuong,
  ma_dich_vu::TEXT                                                   AS danh_sach_ma_dich_vu,
  ten_dich_vu::TEXT                                                  AS danh_sach_dich_vu,
  COALESCE(profile_active, FALSE)::BOOLEAN                           AS ho_so_dang_hoat_dong,
  COALESCE(profile_deleted, FALSE)::BOOLEAN                          AS ho_so_da_xoa,
  updated_at::DATE                                                   AS ngay_cap_nhat

FROM latest
WHERE rn = 1