/* =============================================================================
  sqlmesh_work.src_tbl_dim_plhiv
   =================
   Dimension: người nhiễm HIV (PLHIV).
   Grain: MA_PLHIV – một dòng per bệnh nhân (bản cập nhật mới nhất).

  Nguồn: sqlmesh_work.stg_hiv_aids
   - so_dinh_danh      → MA_PLHIV
   - gioi_tinh         → GIOI_TINH   (mã số → chuỗi chuẩn)
   - ngay_sinh         → NHOM_TUOI   (tính tuổi tại ngày chẩn đoán)
   - ma_tinh_*         → MA_TINH
   - nhom_doi_tuong    → NHOM_NGUY_CO + DUONG_LAY
   - ngay_kd_hiv       → NGAY_CHAN_DOAN
   - ma_tinh_trang_dk  → TRANG_THAI  ('9' = TU_VONG)
   - nguon_du_lieu     → KENH_PHAT_HIEN
============================================================================= */
MODEL (
  name        sqlmesh_work.src_tbl_dim_plhiv,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_plhiv
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_plhiv,
  tags        (dimension, hiv, plhiv),
  description 'HIV patient (PLHIV) dimension – latest demographics and status per patient.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY so_dinh_danh
      ORDER BY thoi_gian_cap_nhat DESC
    ) AS rn
  FROM sqlmesh_work.stg_hiv_aids
  WHERE so_dinh_danh IS NOT NULL
    AND ngay_kd_hiv   IS NOT NULL
    -- Bắt buộc có mã tỉnh để đảm bảo FK về TBL_DON_VI_HANH_CHINH
    AND COALESCE(ma_tinh_thuong_tru, ma_tinh_hien_tai) IS NOT NULL
)

SELECT
  -- Khóa chính
  so_dinh_danh::VARCHAR(20)                                          AS ma_plhiv,

  -- Giới tính
  CASE gioi_tinh
    WHEN '1' THEN 'NAM'
    WHEN '2' THEN 'NU'
    ELSE          'KHONG_XAC_DINH'
  END::VARCHAR(50)                                                   AS gioi_tinh,

  -- Nhóm tuổi tại thời điểm chẩn đoán
  CASE
    WHEN ngay_sinh IS NULL
      THEN 'KHONG_XAC_DINH'
    WHEN EXTRACT(YEAR FROM AGE(ngay_kd_hiv::DATE, ngay_sinh::DATE)) < 15
      THEN '<15'
    WHEN EXTRACT(YEAR FROM AGE(ngay_kd_hiv::DATE, ngay_sinh::DATE)) BETWEEN 15 AND 24
      THEN '15-24'
    WHEN EXTRACT(YEAR FROM AGE(ngay_kd_hiv::DATE, ngay_sinh::DATE)) BETWEEN 25 AND 34
      THEN '25-34'
    WHEN EXTRACT(YEAR FROM AGE(ngay_kd_hiv::DATE, ngay_sinh::DATE)) BETWEEN 35 AND 44
      THEN '35-44'
    WHEN EXTRACT(YEAR FROM AGE(ngay_kd_hiv::DATE, ngay_sinh::DATE)) BETWEEN 45 AND 54
      THEN '45-54'
    ELSE '>=55'
  END::VARCHAR(50)                                                   AS nhom_tuoi,

  -- Tỉnh (ưu tiên thường trú, fallback hiện tại)
  COALESCE(ma_tinh_thuong_tru, ma_tinh_hien_tai)::VARCHAR(10)       AS ma_tinh,

  -- Nhóm nguy cơ (từ mã nhóm đối tượng BYT-IOC)
  CASE nhom_doi_tuong
    WHEN '1' THEN 'MSM'               -- Nam quan hệ tình dục với nam
    WHEN '2' THEN 'TCMT'              -- Tiêm chích ma túy
    WHEN '3' THEN 'PNMD'              -- Phụ nữ mại dâm
    WHEN '4' THEN 'BAN_TINH_PLHIV'   -- Bạn tình PLHIV
    WHEN '5' THEN 'ME_SANG_CON'       -- Mẹ sang con
    WHEN '6' THEN 'CON_ME_NHIEM'      -- Con của mẹ nhiễm HIV
    ELSE          'KHAC'
  END::VARCHAR(50)                                                   AS nhom_nguy_co,

  -- Đường lây truyền (suy luận từ nhóm nguy cơ)
  CASE nhom_doi_tuong
    WHEN '1' THEN 'TINH_DUC_DONG_GIOI'
    WHEN '2' THEN 'TIEM_CHICH_MA_TUY'
    WHEN '3' THEN 'TINH_DUC_DI_GIOI'
    WHEN '4' THEN 'TINH_DUC_DI_GIOI'
    WHEN '5' THEN 'DOC_TRUYEN_TU_ME'
    WHEN '6' THEN 'DOC_TRUYEN_TU_ME'
    ELSE          'KHONG_XAC_DINH'
  END::VARCHAR(50)                                                   AS duong_lay,

  ngay_kd_hiv::DATE                                                  AS ngay_chan_doan,

  -- Trạng thái sống: mã tình trạng '9' = tử vong
  CASE
    WHEN ma_tinh_trang_dk LIKE '%9%' THEN 'TU_VONG'
    ELSE                                   'DANG_SONG'
  END::VARCHAR(50)                                                   AS trang_thai,

  -- Ngày tử vong: không lưu trong BYT-IOC, để NULL
  NULL::DATE                                                         AS ngay_tu_vong,

  COALESCE(nguon_du_lieu, 'KHONG_XAC_DINH')::VARCHAR(50)            AS kenh_phat_hien,

  thoi_gian_cap_nhat::DATE                                           AS ngay_cap_nhat

FROM latest
WHERE rn = 1
