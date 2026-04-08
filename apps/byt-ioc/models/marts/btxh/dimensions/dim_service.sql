/* =============================================================================
  sqlmesh_work.src_btxh_dim_dich_vu
   =================================
   Dimension: danh mục dịch vụ BTXH.
   Grain: MA_DICH_VU – một dòng per service code.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_dim_dich_vu,
  kind        FULL,
  owner       data_team,
  cron        '@daily',
  grain       ma_dich_vu,
  tags        (dimension, btxh, service),
  description 'BTXH service dimension – distinct service codes and labels observed in center profiles.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY center_profile_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_center_profiles
  WHERE NULLIF(ma_dich_vu, '') IS NOT NULL
),
service_codes AS (
  SELECT
    code.ordinality,
    NULLIF(BTRIM(code.service_code), '') AS ma_dich_vu,
    updated_at
  FROM latest l
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(l.ma_dich_vu, ',')) WITH ORDINALITY AS code(service_code, ordinality)
  WHERE l.rn = 1
),
service_names AS (
  SELECT
    name.ordinality,
    NULLIF(BTRIM(name.service_name), '') AS ten_dich_vu,
    updated_at
  FROM latest l
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(COALESCE(l.ten_dich_vu, ''), ',')) WITH ORDINALITY AS name(service_name, ordinality)
  WHERE l.rn = 1
),
ranked AS (
  SELECT
    c.ma_dich_vu,
    n.ten_dich_vu,
    c.updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY c.ma_dich_vu
      ORDER BY c.updated_at DESC NULLS LAST, n.ten_dich_vu DESC NULLS LAST
    ) AS rn
  FROM service_codes c
  LEFT JOIN service_names n
    ON n.ordinality = c.ordinality
)

SELECT
  ma_dich_vu::VARCHAR(50)                                           AS ma_dich_vu,
  COALESCE(ten_dich_vu, 'KHONG_XAC_DINH')::VARCHAR(255)             AS ten_dich_vu,
  updated_at::DATE                                                  AS ngay_cap_nhat
FROM ranked
WHERE rn = 1
  AND ma_dich_vu IS NOT NULL