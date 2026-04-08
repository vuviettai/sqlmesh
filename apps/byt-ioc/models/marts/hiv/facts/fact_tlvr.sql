/* =============================================================================
  sqlmesh_work.src_hiv_fact_tai_luong_vi_rut
   =========================================
   Fact: xét nghiệm tải lượng vi-rút (TLVR) per bệnh nhân per ngày xét nghiệm.
   Grain: (MA_PLHIV, NGAY_XET_NGHIEM) – khớp UNIQUE constraint đích.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_hiv_fact_tai_luong_vi_rut,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  [ma_nguoi_nhiem_hiv, ngay_xet_nghiem]
  ),
  owner       data_team,
  cron        '@daily',
  grain       [ma_nguoi_nhiem_hiv, ngay_xet_nghiem],
  tags        (fact, hiv, viral_load),
  description 'Viral-load (TLVR) test facts – one row per patient per test date.'
);

WITH latest_tlvr AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY so_dinh_danh, ngay_xn_tlvr
      ORDER BY thoi_gian_cap_nhat DESC
    ) AS rn
  FROM sqlmesh_work.stg_hiv_aids
  WHERE so_dinh_danh IS NOT NULL
    AND ngay_xn_tlvr  IS NOT NULL
    AND ma_cskc_b     IS NOT NULL
),

earliest_arv AS (
  SELECT
    so_dinh_danh,
    MIN(ngay_bd_dt_arv) AS ngay_bd_dt_arv
  FROM sqlmesh_work.stg_hiv_aids
  WHERE ngay_bd_dt_arv IS NOT NULL
  GROUP BY so_dinh_danh
)

SELECT
  t.so_dinh_danh::VARCHAR(20)                                        AS ma_nguoi_nhiem_hiv,
  t.ma_cskc_b::VARCHAR(20)                                           AS ma_co_so,
  t.ngay_xn_tlvr::DATE                                               AS ngay_xet_nghiem,
  COALESCE(
    CASE
      WHEN t.kq_xn_tlvr ~ '^\d+(\.\d+)?$'
        THEN ROUND(t.kq_xn_tlvr::NUMERIC)::INT
      WHEN t.kq_xn_tlvr ILIKE '%không phát hiện%'
        OR  t.kq_xn_tlvr ILIKE '%undetectable%'
        THEN 0
      WHEN t.kq_xn_tlvr ~ '^<\s*\d+'
        THEN 0
      WHEN t.kq_xn_tlvr ~ '^>\s*\d+'
        THEN REGEXP_REPLACE(t.kq_xn_tlvr, '[^0-9]', '', 'g')::INT
      ELSE NULL
    END,
    0
  )::INT                                                              AS so_ban_sao_vi_rut,
  CASE
    WHEN t.kq_xn_tlvr IS NULL                                             THEN FALSE
    WHEN t.kq_xn_tlvr ~ '^\d+(\.\d+)?$'                                  THEN TRUE
    WHEN t.kq_xn_tlvr ILIKE '%không phát hiện%'
      OR  t.kq_xn_tlvr ILIKE '%undetectable%'                             THEN TRUE
    WHEN t.kq_xn_tlvr ~ '^[<>]\s*\d+'                                     THEN TRUE
    ELSE FALSE
  END::BOOLEAN                                                         AS la_ket_qua_hop_le,
  CASE
    WHEN a.ngay_bd_dt_arv IS NOT NULL
      AND t.ngay_xn_tlvr >= a.ngay_bd_dt_arv
    THEN (
        EXTRACT(YEAR  FROM AGE(t.ngay_xn_tlvr::DATE, a.ngay_bd_dt_arv::DATE)) * 12
      + EXTRACT(MONTH FROM AGE(t.ngay_xn_tlvr::DATE, a.ngay_bd_dt_arv::DATE))
    )::INT
    ELSE NULL
  END                                                                   AS thoi_gian_dieu_tri_thang
FROM latest_tlvr t
LEFT JOIN earliest_arv a ON a.so_dinh_danh = t.so_dinh_danh
WHERE t.rn = 1