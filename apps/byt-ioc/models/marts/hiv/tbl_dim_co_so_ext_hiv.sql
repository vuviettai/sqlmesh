/* =============================================================================
  sqlmesh_work.src_tbl_dim_co_so_ext_hiv
   ==========================
   Dimension: thông tin năng lực HIV của từng cơ sở.
   Grain: MA_CO_SO – một dòng per cơ sở.

  Nguồn: tổng hợp từ sqlmesh_work.stg_hiv_aids
   - LA_CO_SO_DIEU_TRI   = TRUE nếu cơ sở có bản ghi điều trị ARV
   - LA_CO_SO_XET_NGHIEM = TRUE nếu cơ sở có bản ghi xét nghiệm TLVR
   - LA_CO_SO_PREP       = FALSE (dữ liệu PrEP chưa có trong nguồn BYT-IOC)

   Rebuild toàn bộ (FULL) mỗi ngày để cập nhật khi cơ sở mới xuất hiện.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_tbl_dim_co_so_ext_hiv,
  kind        FULL,
  owner       data_team,
  cron        '@daily',
  grain       ma_co_so,
  tags        (dimension, hiv, facility),
  description 'HIV facility extension – flags ARV treatment, VL testing, and PrEP capability per facility.'
);

WITH arv_sites AS (
  -- Cơ sở có dữ liệu điều trị ARV
  SELECT DISTINCT
    COALESCE(noi_bd_dt_arv, ma_cskc_b) AS ma_co_so,
    TRUE                                AS la_co_so_dieu_tri
  FROM sqlmesh_work.stg_hiv_aids
  WHERE COALESCE(noi_bd_dt_arv, ma_cskc_b) IS NOT NULL
    AND ngay_bd_dt_arv IS NOT NULL
),

xn_sites AS (
  -- Cơ sở có dữ liệu xét nghiệm TLVR
  SELECT DISTINCT
    ma_cskc_b  AS ma_co_so,
    TRUE       AS la_co_so_xet_nghiem
  FROM sqlmesh_work.stg_hiv_aids
  WHERE ma_cskc_b   IS NOT NULL
    AND ngay_xn_tlvr IS NOT NULL
),

all_sites AS (
  SELECT ma_co_so FROM arv_sites
  UNION
  SELECT ma_co_so FROM xn_sites
)

SELECT
  f.ma_co_so::VARCHAR(20)                          AS ma_co_so,
  COALESCE(a.la_co_so_dieu_tri,    FALSE)::BOOLEAN AS la_co_so_dieu_tri,
  COALESCE(x.la_co_so_xet_nghiem, FALSE)::BOOLEAN AS la_co_so_xet_nghiem,
  FALSE::BOOLEAN                                   AS la_co_so_prep

FROM      all_sites f
LEFT JOIN arv_sites a USING (ma_co_so)
LEFT JOIN xn_sites  x USING (ma_co_so)
