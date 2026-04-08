/* =============================================================================
  sqlmesh_work.src_btxh_dim_nguoi_thu_huong
   ========================================
   Dimension: người thụ hưởng BTXH.
   Grain: MA_NGUOI_THU_HUONG – một dòng per beneficiary (bản cập nhật mới nhất).
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_dim_nguoi_thu_huong,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_nguoi_thu_huong
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_nguoi_thu_huong,
  tags        (dimension, btxh, beneficiary),
  description 'BTXH beneficiary dimension – latest demographics and current support status per beneficiary.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY beneficiary_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_beneficiaries
  WHERE beneficiary_id IS NOT NULL
)

SELECT
  beneficiary_id::VARCHAR(64)                                        AS ma_nguoi_thu_huong,
  ho_va_ten::VARCHAR(255)                                            AS ho_va_ten,
  gioi_tinh::VARCHAR(50)                                             AS gioi_tinh,
  ngay_sinh::DATE                                                    AS ngay_sinh,

  CASE
    WHEN ngay_sinh IS NULL THEN 'KHONG_XAC_DINH'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, ngay_sinh::DATE)) < 16 THEN '<16'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, ngay_sinh::DATE)) BETWEEN 16 AND 24 THEN '16-24'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, ngay_sinh::DATE)) BETWEEN 25 AND 44 THEN '25-44'
    WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, ngay_sinh::DATE)) BETWEEN 45 AND 59 THEN '45-59'
    ELSE '>=60'
  END::VARCHAR(50)                                                   AS nhom_tuoi,

  COALESCE(NULLIF(ma_tinh_moi, ''), NULLIF(ma_tinh_hien_tai, ''), '00')::VARCHAR(10)
                                                                     AS ma_tinh,
  COALESCE(NULLIF(dia_chi_moi, ''), dia_chi_hien_tai)::TEXT          AS dia_chi,
  dan_toc::VARCHAR(50)                                               AS dan_toc,
  quoc_tich::VARCHAR(50)                                             AS quoc_tich,
  noi_sinh::VARCHAR(255)                                             AS noi_sinh,
  so_giay_to::VARCHAR(50)                                            AS so_giay_to,
  ma_loai_giay_to::VARCHAR(20)                                       AS ma_loai_giay_to,
  ma_co_so_hien_tai::VARCHAR(30)                                     AS ma_co_so_hien_tai,
  ten_co_so_hien_tai::VARCHAR(255)                                   AS ten_co_so_hien_tai,

  CASE
    WHEN is_active IS TRUE THEN 'DANG_HOAT_DONG'
    ELSE 'NGUNG_HOAT_DONG'
  END::VARCHAR(50)                                                   AS trang_thai_nguoi_thu_huong,

  COALESCE(ma_trang_thai_ho_so, 'KHONG_CO_HO_SO')::VARCHAR(50)      AS trang_thai_ho_so,
  COALESCE(co_ho_so_trung_tam, FALSE)::BOOLEAN                       AS co_ho_so_trung_tam,
  COALESCE(so_ho_so_trung_tam, 0)::INT                               AS so_ho_so_trung_tam,
  COALESCE(so_ho_so_trung_tam_hoat_dong, 0)::INT                     AS so_ho_so_trung_tam_hoat_dong,
  updated_at::DATE                                                   AS ngay_cap_nhat

FROM latest
WHERE rn = 1