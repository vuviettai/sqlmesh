/* =============================================================================
  sqlmesh_work.src_hiv_fact_dieu_tri_arv
   =====================================
   Fact: đợt điều trị ARV per bệnh nhân.
   Grain: (MA_PLHIV, NGAY_BAT_DAU_ARV) – một dòng per đợt điều trị.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_hiv_fact_dieu_tri_arv,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  [ma_nguoi_nhiem_hiv, ngay_bat_dau_arv]
  ),
  owner       data_team,
  cron        '@daily',
  grain       [ma_nguoi_nhiem_hiv, ngay_bat_dau_arv],
  tags        (fact, hiv, arv),
  description 'ARV treatment facts – one row per patient treatment episode.'
);

WITH latest_arv AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY so_dinh_danh, ngay_bd_dt_arv
      ORDER BY thoi_gian_cap_nhat DESC
    ) AS rn
  FROM sqlmesh_work.stg_hiv_aids
  WHERE so_dinh_danh IS NOT NULL
    AND ngay_bd_dt_arv IS NOT NULL
    AND COALESCE(noi_bd_dt_arv, ma_cskc_b) IS NOT NULL
)

SELECT
  so_dinh_danh::VARCHAR(20)                                         AS ma_nguoi_nhiem_hiv,
  COALESCE(noi_bd_dt_arv, ma_cskc_b)::VARCHAR(20)                  AS ma_co_so,
  ngay_bd_dt_arv::DATE                                              AS ngay_bat_dau_arv,
  ngay_kt_xu_tri::DATE                                              AS ngay_ket_thuc_arv,
  CASE
    WHEN ma_tinh_trang_dk LIKE '%9%'   THEN 'TU_VONG'
    WHEN ngay_kt_xu_tri   IS NOT NULL  THEN 'NGUNG_DIEU_TRI'
    ELSE                                    'DANG_DIEU_TRI'
  END::VARCHAR(50)                                                  AS trang_thai_dieu_tri,
  COALESCE(ma_phac_do_dieu_tri, ma_phac_do_bd)::VARCHAR(50)        AS phac_do,
  COALESCE(nguon_du_lieu, 'KHONG_XAC_DINH')::VARCHAR(50)           AS kenh_quan_ly
FROM latest_arv
WHERE rn = 1