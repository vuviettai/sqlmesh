/* =============================================================================
  sqlmesh_work.src_btxh_dim_co_so
   ==============================
   Dimension: cơ sở BTXH.
   Grain: MA_CO_SO – một dòng per facility (bản cập nhật mới nhất).
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_dim_co_so,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_co_so
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_co_so,
  tags        (dimension, btxh, facility),
  description 'BTXH facility dimension – latest facility master data with fallback to observed center profile identifiers.'
);

WITH master_latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY facility_code
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_facilities
  WHERE facility_code IS NOT NULL
),
observed_latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY ma_co_so
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_center_profiles
  WHERE ma_co_so IS NOT NULL
)

SELECT
  COALESCE(m.facility_code, o.ma_co_so)::VARCHAR(30)                              AS ma_co_so,
  COALESCE(NULLIF(m.facility_name, ''), NULLIF(o.ten_co_so, ''), 'KHONG_XAC_DINH')::VARCHAR(255)
                                                                                   AS ten_co_so,
  COALESCE(m.facility_id, o.facility_id)::VARCHAR(64)                              AS ma_dinh_danh_nguon_co_so,
  COALESCE(m.center_type_code, 'KHONG_XAC_DINH')::VARCHAR(50)                      AS ma_loai_trung_tam,
  COALESCE(m.center_type_name, 'KHONG_XAC_DINH')::VARCHAR(255)                     AS ten_loai_trung_tam,
  COALESCE(m.facility_form, 'KHONG_XAC_DINH')::VARCHAR(50)                         AS ma_hinh_thuc_co_so,
  COALESCE(m.facility_form_name, 'KHONG_XAC_DINH')::VARCHAR(255)                   AS ten_hinh_thuc_co_so,
  m.management_unit_code::VARCHAR(50)                                              AS ma_don_vi_quan_ly,
  m.management_unit_name::VARCHAR(255)                                             AS ten_don_vi_quan_ly,
  m.province_code::VARCHAR(10)                                                     AS ma_tinh,
  m.contact_address::TEXT                                                          AS dia_chi,
  COALESCE(m.phone_number, '')::VARCHAR(50)                                        AS so_dien_thoai,
  COALESCE(m.email, '')::VARCHAR(255)                                              AS thu_dien_tu,
  COALESCE(m.director_name, '')::VARCHAR(255)                                      AS ten_giam_doc,
  COALESCE(m.is_active, TRUE)::BOOLEAN                                             AS dang_hoat_dong,
  (o.ma_co_so IS NOT NULL)::BOOLEAN                                                AS da_phat_sinh_ho_so,
  COALESCE(m.updated_at, o.updated_at)::DATE                                       AS ngay_cap_nhat
FROM master_latest m
FULL OUTER JOIN observed_latest o
  ON o.ma_co_so = m.facility_code
WHERE COALESCE(m.rn, o.rn) = 1
