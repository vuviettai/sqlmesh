BEGIN;

CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS public.hiv_dim_nguoi_nhiem_hiv (
    ma_nguoi_nhiem_hiv VARCHAR(20) PRIMARY KEY,
    gioi_tinh VARCHAR(50),
    nhom_tuoi VARCHAR(50),
    ma_tinh VARCHAR(10),
    nhom_nguy_co VARCHAR(50),
    duong_lay VARCHAR(50),
    ngay_chan_doan DATE,
    trang_thai VARCHAR(50),
    ngay_tu_vong DATE,
    kenh_phat_hien VARCHAR(50),
    ngay_cap_nhat DATE
);

CREATE TABLE IF NOT EXISTS public.hiv_dim_co_so_mo_rong (
    ma_co_so VARCHAR(20) PRIMARY KEY,
    la_co_so_dieu_tri BOOLEAN,
    la_co_so_xet_nghiem BOOLEAN,
    la_co_so_prep BOOLEAN
);

CREATE TABLE IF NOT EXISTS public.hiv_fact_dieu_tri_arv (
    ma_nguoi_nhiem_hiv VARCHAR(20) NOT NULL,
    ma_co_so VARCHAR(20),
    ngay_bat_dau_arv DATE NOT NULL,
    ngay_ket_thuc_arv DATE,
    trang_thai_dieu_tri VARCHAR(50),
    phac_do VARCHAR(50),
    kenh_quan_ly VARCHAR(50),
    PRIMARY KEY (ma_nguoi_nhiem_hiv, ngay_bat_dau_arv)
);

CREATE TABLE IF NOT EXISTS public.hiv_fact_tai_luong_vi_rut (
    ma_nguoi_nhiem_hiv VARCHAR(20) NOT NULL,
    ma_co_so VARCHAR(20),
    ngay_xet_nghiem DATE NOT NULL,
    so_ban_sao_vi_rut INTEGER,
    la_ket_qua_hop_le BOOLEAN,
    thoi_gian_dieu_tri_thang INTEGER,
    PRIMARY KEY (ma_nguoi_nhiem_hiv, ngay_xet_nghiem)
);

CREATE INDEX IF NOT EXISTS idx_hiv_dim_nguoi_nhiem_hiv_ma_tinh
    ON public.hiv_dim_nguoi_nhiem_hiv (ma_tinh);

CREATE INDEX IF NOT EXISTS idx_hiv_fact_dieu_tri_arv_ma_co_so
    ON public.hiv_fact_dieu_tri_arv (ma_co_so);

CREATE INDEX IF NOT EXISTS idx_hiv_fact_tai_luong_vi_rut_ma_co_so
    ON public.hiv_fact_tai_luong_vi_rut (ma_co_so);

CREATE INDEX IF NOT EXISTS idx_hiv_fact_tai_luong_vi_rut_ngay_xet_nghiem
    ON public.hiv_fact_tai_luong_vi_rut (ngay_xet_nghiem);

COMMIT;
