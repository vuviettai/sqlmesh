/* =============================================================================
  sqlmesh_work.src_btxh_fact_lich_su_cong_tac_nhan_vien_ctxh
   =========================================================
   Fact: lịch sử công tác của nhân viên CTXH.
   Grain: WORK_HISTORY_ID – một dòng per work history item.
============================================================================= */
MODEL (
  name        sqlmesh_work.src_btxh_fact_lich_su_cong_tac_nhan_vien_ctxh,
  kind        INCREMENTAL_BY_UNIQUE_KEY (
    unique_key  ma_lich_su_cong_tac
  ),
  owner       data_team,
  cron        '@daily',
  grain       ma_lich_su_cong_tac,
  tags        (fact, btxh, social_worker_work_history),
  description 'BTXH social worker work history fact – one row per work history record.'
);

WITH latest AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY work_history_id
      ORDER BY updated_at DESC NULLS LAST, _airbyte_extracted_at DESC NULLS LAST
    ) AS rn
  FROM sqlmesh_work.stg_btxh_work_histories
  WHERE work_history_id IS NOT NULL
    AND social_worker_id IS NOT NULL
)

SELECT
  work_history_id::VARCHAR(64)                                      AS ma_lich_su_cong_tac,
  social_worker_id::VARCHAR(64)                                     AS ma_nhan_vien_ctxh,
  facility_code::VARCHAR(30)                                        AS ma_co_so,
  facility_name::VARCHAR(255)                                       AS ten_co_so,
  facility_type::VARCHAR(50)                                        AS loai_co_so,
  start_date::DATE                                                  AS ngay_bat_dau,
  end_date::DATE                                                    AS ngay_ket_thuc,
  COALESCE(is_current, FALSE)::BOOLEAN                              AS la_cong_tac_hien_tai,
  status::VARCHAR(50)                                               AS trang_thai,
  position_code::VARCHAR(50)                                        AS ma_vi_tri,
  position_name::VARCHAR(255)                                       AS ten_vi_tri,
  contract_type_code::VARCHAR(50)                                   AS ma_loai_hop_dong,
  contract_type_name::VARCHAR(255)                                  AS ten_loai_hop_dong,
  job_description::TEXT                                             AS mo_ta_cong_viec,
  updated_at::DATE                                                  AS ngay_cap_nhat
FROM latest
WHERE rn = 1