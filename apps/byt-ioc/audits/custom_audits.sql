/* =============================================================================
   Custom audits for byt-ioc project
============================================================================= */

/* Every patient record must have a national ID (soDinhDanh). */
AUDIT (
  name assert_so_dinh_danh_not_null
);
SELECT *
FROM @this_model
WHERE so_dinh_danh IS NULL;

/* HIV confirmation date must not be in the future. */
AUDIT (
  name assert_ngay_kd_hiv_not_future
);
SELECT *
FROM @this_model
WHERE ngay_kd_hiv > CURRENT_DATE;

/* ARV start date must not be before HIV confirmation date. */
AUDIT (
  name assert_arv_after_hiv_confirmation
);
SELECT arv.ma_plhiv,
       plhiv.ngay_chan_doan,
       arv.ngay_bat_dau_arv
FROM public.tbl_fact_arv   AS arv
JOIN public.tbl_dim_plhiv  AS plhiv ON plhiv.ma_plhiv = arv.ma_plhiv
WHERE arv.ngay_bat_dau_arv < plhiv.ngay_chan_doan;

/* Viral-load test date must be on or after ARV start date. */
AUDIT (
  name assert_tlvr_after_arv_start
);
SELECT tlvr.ma_plhiv,
       arv.ngay_bat_dau_arv,
       tlvr.ngay_xet_nghiem
FROM public.tbl_fact_tlvr  AS tlvr
JOIN public.tbl_fact_arv   AS arv ON arv.ma_plhiv = tlvr.ma_plhiv
WHERE tlvr.ngay_xet_nghiem < arv.ngay_bat_dau_arv;
