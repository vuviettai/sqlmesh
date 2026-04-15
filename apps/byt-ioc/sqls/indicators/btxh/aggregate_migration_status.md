# BTXH Aggregate Migration Status

## Migrated to aggregate/public models

- `I.1.1-songuoidangduoctrogiup.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `I.1.2-tilenguoicaotuoi-khuyettat-treem-trentongdanso.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `II.1.2-tyledoituongtgxhtrentongdanso.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `I.4.3-tongsocoso.sql` -> `public.btxh_dim_co_so`
- `I.4.4-tongsogiuong-choovatrinhtrangsudung.sql` -> `public.btxh_agg_dich_vu_co_so`
- `II.1.4-songuoicaotuoihuongtgxh.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `II.1.5-songuoidonthanhuongtgxh.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `II.1.6-songuoihivhuongtgxh.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `II.1.7-sotreemhuongtgxh.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `II.1.8-songuoikhuyettathuongtgxh.sql` -> `public.btxh_agg_nguoi_thu_huong`
- `II.4.5-cocautoituongtheodotuoi.sql` -> `public.btxh_agg_nguoi_thu_huong`

## Still blocked on missing public models

- trợ cấp: `II.1.1`, `II.4.1`, `II.4.4`, `III.1.6`
- chi phí: `I.2.4`, `I.2.5`, `III.2.1`, `IV.2.1`
- can thiệp: `I.1.4`, `I.2.3`
- hồ sơ / số hóa hồ sơ: `I.4.1`, `I.4.2`, `II.4.2`, `III.3.1`
- người khuyết tật chuyên biệt: `III.1.1`, `III.1.2`, `III.1.3`, `III.1.4`, `III.1.5`, `III.1.7`, `III.1.8`
- nhân sự theo lĩnh vực công tác / nguồn lương / trạng thái chi tiết: `I.1.6`, `I.2.2`, `IV.1.1`, `IV.1.2-1.3`, `IV.1.4`, `IV.1.5`, `IV.1.6`, `IV.1.7`, `IV.1.8`, `IV.2.2`, `IV.3.1`

## Notes

- `public.btxh_agg_nguoi_thu_huong` now exposes both `nhom_tuoi` and `nhom_tuoi_chi_tiet`.
- Legacy `ten_nhom` is not yet available in the public layer, so migrated queries currently expose `ma_nhom_doi_tuong` as a fallback display value.
- Current migrated indicators use `trang_thai_nguoi_thu_huong = 'DANG_HOAT_DONG'` as the active-beneficiary filter because the public layer does not yet expose legacy `nam_ket_thuc / thang_ket_thuc / ngay_ket_thuc` fields.