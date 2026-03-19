/* =============================================================================
  sqlmesh_work.src_tbl_fact_tlvr
   =================
   Fact: xét nghiệm tải lượng vi-rút (TLVR) per bệnh nhân per ngày xét nghiệm.
   Grain: (MA_PLHIV, NGAY_XET_NGHIEM) – khớp UNIQUE constraint đích.

  Nguồn: sqlmesh_work.stg_hiv_aids
   - so_dinh_danh    → MA_PLHIV
   - ma_cskc_b       → MA_CO_SO (cơ sở thực hiện xét nghiệm)
   - ngay_xn_tlvr    → NGAY_XET_NGHIEM
   - kq_xn_tlvr      → KET_QUA_COPIES  (text → int, xử lý các giá trị đặc biệt)
   - THOI_GIAN_DIEU_TRI_THANG = khoảng cách (tháng) giữa ngày bắt đầu ARV
     sớm nhất và ngày xét nghiệm.

   Nếu cùng patient + test date xuất hiện nhiều lần → giữ bản mới nhất.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_tbl_fact_tlvr,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  [ma_plhiv, ngay_xet_nghiem]
  ),
  owner       data_team,
  cron        '@daily',
  grain       [ma_plhiv, ngay_xet_nghiem],
  tags        (fact, hiv, viral_load),
  description 'Viral-load (TLVR) test facts – one row per patient per test date.'
);

WITH latest_tlvr AS (
  -- Giữ bản cập nhật mới nhất per (bệnh nhân, ngày xét nghiệm)
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
  -- Ngày bắt đầu ARV sớm nhất per bệnh nhân (để tính thời gian điều trị)
  SELECT
    so_dinh_danh,
    MIN(ngay_bd_dt_arv) AS ngay_bd_dt_arv
  FROM sqlmesh_work.stg_hiv_aids
  WHERE ngay_bd_dt_arv IS NOT NULL
  GROUP BY so_dinh_danh
)

SELECT
  t.so_dinh_danh::VARCHAR(20)                                        AS ma_plhiv,

  t.ma_cskc_b::VARCHAR(20)                                           AS ma_co_so,

  t.ngay_xn_tlvr::DATE                                               AS ngay_xet_nghiem,

  -- Chuyển kết quả text → số bản sao (copies/mL)
  -- Xử lý: số thuần, "< 20", "> 100000", "không phát hiện", NULL → 0
  COALESCE(
    CASE
      WHEN t.kq_xn_tlvr ~ '^\d+(\.\d+)?$'
        THEN ROUND(t.kq_xn_tlvr::NUMERIC)::INT
      WHEN t.kq_xn_tlvr ILIKE '%không phát hiện%'
        OR  t.kq_xn_tlvr ILIKE '%undetectable%'
        THEN 0
      WHEN t.kq_xn_tlvr ~ '^<\s*\d+'
        THEN 0   -- dưới ngưỡng phát hiện
      WHEN t.kq_xn_tlvr ~ '^>\s*\d+'
        THEN REGEXP_REPLACE(t.kq_xn_tlvr, '[^0-9]', '', 'g')::INT
      ELSE NULL
    END,
    0
  )::INT                                                              AS ket_qua_copies,

  -- Đánh dấu kết quả hợp lệ (có thể parse được)
  CASE
    WHEN t.kq_xn_tlvr IS NULL                                             THEN FALSE
    WHEN t.kq_xn_tlvr ~ '^\d+(\.\d+)?$'                                  THEN TRUE
    WHEN t.kq_xn_tlvr ILIKE '%không phát hiện%'
      OR  t.kq_xn_tlvr ILIKE '%undetectable%'                             THEN TRUE
    WHEN t.kq_xn_tlvr ~ '^[<>]\s*\d+'                                     THEN TRUE
    ELSE FALSE
  END::BOOLEAN                                                         AS la_ket_qua_hop_le,

  -- Thời gian điều trị ARV (tháng) tính đến ngày xét nghiệm
  CASE
    WHEN a.ngay_bd_dt_arv IS NOT NULL
      AND t.ngay_xn_tlvr >= a.ngay_bd_dt_arv
    THEN (
        EXTRACT(YEAR  FROM AGE(t.ngay_xn_tlvr::DATE, a.ngay_bd_dt_arv::DATE)) * 12
      + EXTRACT(MONTH FROM AGE(t.ngay_xn_tlvr::DATE, a.ngay_bd_dt_arv::DATE))
    )::INT
    ELSE NULL
  END                                                                   AS thoi_gian_dieu_tri_thang

FROM latest_tlvr     t
LEFT JOIN earliest_arv a ON a.so_dinh_danh = t.so_dinh_danh
WHERE t.rn = 1
