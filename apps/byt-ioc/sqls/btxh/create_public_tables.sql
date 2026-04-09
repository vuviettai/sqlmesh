/* =============================================================================
  BTXH – Public schema DDL
  Target database: BI database, schema: public
  Generated for: byt-ioc SQLMesh project

  Table layout
  ────────────
    • Some models materialise a surrogate id BIGINT PRIMARY KEY, assigned by
        SQLMesh model logic (auto-increments across runs; NOT a serial).
    • Other models use their natural/business key directly as the primary key.
    • All other columns mirror the SQLMesh model SELECT output exactly.

  Indexes
  ───────
  Foreign-key columns that are frequently joined are indexed separately.

  Usage
  ─────
  Run once against the target database to create the schema.
  Safe to re-run (IF NOT EXISTS everywhere).
============================================================================= */

BEGIN;

-- ---------------------------------------------------------------------------
-- DIMENSIONS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.btxh_dim_nguoi_thu_huong (
    ma_nguoi_thu_huong              VARCHAR(64)     NOT NULL,
    ho_va_ten                       VARCHAR(255),
    gioi_tinh                       VARCHAR(50),
    nam_sinh                        INTEGER,
    thang_sinh                      INTEGER,
    ngay_sinh                       INTEGER,        -- day-of-month extracted from date of birth
    ma_tinh                         VARCHAR(10),
    dia_chi                         TEXT,
    dan_toc                         VARCHAR(50),
    quoc_tich                       VARCHAR(50),
    noi_sinh                        VARCHAR(255),
    so_giay_to                      VARCHAR(50),
    ma_loai_giay_to                 VARCHAR(20),
    ma_co_so_hien_tai               VARCHAR(30),
    ten_co_so_hien_tai              VARCHAR(255),
    trang_thai_nguoi_thu_huong      VARCHAR(50),
    trang_thai_ho_so                VARCHAR(50),
    co_ho_so_trung_tam              BOOLEAN,
    so_ho_so_trung_tam              INTEGER,
    so_ho_so_trung_tam_hoat_dong    INTEGER,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_nguoi_thu_huong  PRIMARY KEY (ma_nguoi_thu_huong)
);

CREATE TABLE IF NOT EXISTS public.btxh_dim_nhan_vien_ctxh (
    ma_nhan_vien_ctxh               VARCHAR(64)     NOT NULL,
    ho_va_ten                       VARCHAR(255),
    gioi_tinh                       VARCHAR(50),
    ngay_sinh                       DATE,
    ma_dan_toc                      VARCHAR(20),
    ten_dan_toc                     VARCHAR(100),
    ma_quoc_tich                    VARCHAR(20),
    ten_quoc_tich                   VARCHAR(100),
    so_dien_thoai                   VARCHAR(50),
    thu_dien_tu                     VARCHAR(255),
    ma_tinh                         VARCHAR(10),
    dia_chi                         TEXT,
    so_giay_to                      VARCHAR(50),
    ma_loai_giay_to                 VARCHAR(20),
    ten_loai_giay_to                VARCHAR(100),
    ngay_cap_giay_to                DATE,
    noi_cap_giay_to                 VARCHAR(255),
    ma_to_chuc                      VARCHAR(64),
    ma_co_so_hien_tai               VARCHAR(30),
    ten_co_so_hien_tai              VARCHAR(255),
    loai_co_so_hien_tai             VARCHAR(50),
    ma_vi_tri_hien_tai              VARCHAR(50),
    ten_vi_tri_hien_tai             VARCHAR(255),
    ma_loai_hop_dong_hien_tai       VARCHAR(50),
    ten_loai_hop_dong_hien_tai      VARCHAR(255),
    ma_trinh_do_hoc_van             VARCHAR(50),
    ten_trinh_do_hoc_van            VARCHAR(255),
    ma_chuyen_nganh                 VARCHAR(50),
    ten_chuyen_nganh                VARCHAR(255),
    nam_tot_nghiep                  VARCHAR(10),
    so_lich_su_cong_tac             INTEGER,
    so_lich_su_hoc_van              INTEGER,
    so_chung_chi_hanh_nghe          INTEGER,
    dang_hoat_dong                  BOOLEAN,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_nhan_vien_ctxh   PRIMARY KEY (ma_nhan_vien_ctxh)
);

CREATE TABLE IF NOT EXISTS public.btxh_dim_co_so (
    ma_co_so                        VARCHAR(30)     NOT NULL,
    ten_co_so                       VARCHAR(255),
    ma_dinh_danh_nguon_co_so        VARCHAR(64),
    ma_loai_trung_tam               VARCHAR(50),
    ten_loai_trung_tam              VARCHAR(255),
    ma_hinh_thuc_co_so              VARCHAR(50),
    ten_hinh_thuc_co_so             VARCHAR(255),
    ma_don_vi_quan_ly               VARCHAR(50),
    ten_don_vi_quan_ly              VARCHAR(255),
    ma_tinh                         VARCHAR(10),
    dia_chi                         TEXT,
    so_dien_thoai                   VARCHAR(50),
    thu_dien_tu                     VARCHAR(255),
    ten_giam_doc                    VARCHAR(255),
    dang_hoat_dong                  BOOLEAN,
    da_phat_sinh_ho_so              BOOLEAN,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_co_so    PRIMARY KEY (ma_co_so)
);

CREATE TABLE IF NOT EXISTS public.btxh_dim_dich_vu (
    ma_dich_vu                      VARCHAR(50)     NOT NULL,
    ten_dich_vu                     VARCHAR(255),
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_dich_vu  PRIMARY KEY (ma_dich_vu)
);

-- ---------------------------------------------------------------------------
-- FACTS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.btxh_fact_hoat_dong_cham_soc (
    id                              BIGINT          NOT NULL,
    ma_hoat_dong_cham_soc           VARCHAR(64)     NOT NULL,
    ma_nguoi_thu_huong              VARCHAR(64),
    ma_co_so                        VARCHAR(30),
    ma_ke_hoach_cham_soc            VARCHAR(64),
    trang_thai_ke_hoach_cham_soc    VARCHAR(50),
    ma_muc_tieu                     VARCHAR(50),
    mo_ta_muc_tieu                  TEXT,
    muc_do_uu_tien                  VARCHAR(50),
    ten_nguoi_quan_ly               VARCHAR(255),
    ten_lanh_dao_co_so              VARCHAR(255),
    trach_nhiem                     TEXT,
    doi_tuong_hoac_nguoi_giam_ho    TEXT,
    hoat_dong_can_thiep             TEXT,
    ma_linh_vuc_danh_gia            VARCHAR(50),
    nguon_luc_kinh_phi              TEXT,
    rui_ro_va_giai_phap             TEXT,
    dieu_kien_ho_tro                TEXT,
    ngay_lap_ke_hoach               DATE,
    ngay_bat_dau                    DATE,
    ngay_ket_thuc                   DATE,
    ngay_phe_duyet                  DATE,
    ngay_ra_soat                    DATE,
    so_ke_hoach                     VARCHAR(100),
    danh_sach_don_vi_thuc_hien      TEXT,
    so_don_vi_thuc_hien             INTEGER,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_fact_hoat_dong_cham_soc  PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_hoat_dong_cham_soc  UNIQUE      (ma_hoat_dong_cham_soc)
);

COMMENT ON COLUMN public.btxh_fact_hoat_dong_cham_soc.ma_nguoi_thu_huong IS
    'Loaded from CareActivities.carePlan.beneficiaryId, fallback to carePlan.beneficiary.id.';

CREATE TABLE IF NOT EXISTS public.btxh_fact_ho_so_trung_tam (
    id                              BIGINT          NOT NULL,
    ma_ho_so_trung_tam              VARCHAR(64)     NOT NULL,
    ma_nguoi_thu_huong              VARCHAR(64),
    ma_co_so                        VARCHAR(30),
    ngay_tiep_nhan                  DATE,
    ngay_quyet_dinh_tiep_nhan       DATE,
    so_quyet_dinh_tiep_nhan         VARCHAR(100),
    co_so_ban_hanh_quyet_dinh       VARCHAR(255),
    so_quyet_dinh                   VARCHAR(100),
    trang_thai_ho_so                VARCHAR(50),
    loai_luu_tru                    VARCHAR(100),
    ma_nhom_doi_tuong_chinh         VARCHAR(50),
    danh_sach_ma_nhom_doi_tuong     TEXT,
    danh_sach_ma_chi_tiet_doi_tuong TEXT,
    danh_sach_ma_dich_vu            TEXT,
    danh_sach_dich_vu               TEXT,
    ho_so_dang_hoat_dong            BOOLEAN,
    ho_so_da_xoa                    BOOLEAN,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_fact_ho_so_trung_tam PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_ho_so_trung_tam UNIQUE      (ma_ho_so_trung_tam)
);

CREATE TABLE IF NOT EXISTS public.btxh_fact_gan_dich_vu (
    id                              BIGINT          NOT NULL,
    ma_ho_so_trung_tam              VARCHAR(64)     NOT NULL,
    ma_nguoi_thu_huong              VARCHAR(64),
    ma_co_so                        VARCHAR(30),
    ma_dich_vu                      VARCHAR(50)     NOT NULL,
    ten_dich_vu                     VARCHAR(255),
    ngay_tiep_nhan                  DATE,
    ngay_quyet_dinh_tiep_nhan       DATE,
    trang_thai_ho_so                VARCHAR(50),
    loai_luu_tru                    VARCHAR(100),
    ho_so_dang_hoat_dong            BOOLEAN,
    ho_so_da_xoa                    BOOLEAN,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_fact_gan_dich_vu PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_gan_dich_vu UNIQUE      (ma_ho_so_trung_tam, ma_dich_vu)
);

CREATE TABLE IF NOT EXISTS public.btxh_fact_nang_luc_co_so (
    id                                          BIGINT          NOT NULL,
    ma_co_so                                    VARCHAR(30)     NOT NULL,
    ma_dinh_danh_nguon_co_so                    VARCHAR(64),
    ma_loai_trung_tam                           VARCHAR(50),
    ma_hinh_thuc_co_so                          VARCHAR(50),
    cong_suat_ke_hoach                          INTEGER,
    tong_nhan_su                                INTEGER,
    tong_doi_tuong                              INTEGER,
    tong_dien_tich                              DECIMAL(18, 2),
    dien_tich_binh_quan_mot_doi_tuong           DECIMAL(18, 2),
    dien_tich_nha_o_binh_quan_mot_doi_tuong     DECIMAL(18, 2),
    dang_hoat_dong                              BOOLEAN,
    ngay_cap_nhat                               DATE            NOT NULL,
    CONSTRAINT pk_btxh_fact_nang_luc_co_so  PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_nang_luc_co_so  UNIQUE      (ma_co_so, ngay_cap_nhat)
);

CREATE TABLE IF NOT EXISTS public.btxh_fact_lich_su_cong_tac_xh (
    id                              BIGINT          NOT NULL,
    ma_lich_su_cong_tac             VARCHAR(64)     NOT NULL,
    ma_nhan_vien_ctxh               VARCHAR(64),
    ma_co_so                        VARCHAR(30),
    ten_co_so                       VARCHAR(255),
    loai_co_so                      VARCHAR(50),
    ngay_bat_dau                    DATE,
    ngay_ket_thuc                   DATE,
    la_cong_tac_hien_tai            BOOLEAN,
    trang_thai                      VARCHAR(50),
    ma_vi_tri                       VARCHAR(50),
    ten_vi_tri                      VARCHAR(255),
    ma_loai_hop_dong                VARCHAR(50),
    ten_loai_hop_dong               VARCHAR(255),
    mo_ta_cong_viec                 TEXT,
    nguon                           VARCHAR(20),        -- 'WORK_HISTORIES' or 'SOCIAL_WORKERS'
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_fact_lich_su_cong_tac_xh  PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_lich_su_cong_tac_xh  UNIQUE      (ma_lich_su_cong_tac)
);

COMMENT ON COLUMN public.btxh_fact_lich_su_cong_tac_xh.ma_nhan_vien_ctxh IS
    'Loaded from WorkHistories.socialWorker.socialWorkerId, fallback to socialWorker.id.';

-- ---------------------------------------------------------------------------
-- INDEXES  (foreign-key / filter columns)
-- ---------------------------------------------------------------------------

-- dim_nguoi_thu_huong
CREATE INDEX IF NOT EXISTS idx_dim_nth_ma_co_so
    ON public.btxh_dim_nguoi_thu_huong (ma_co_so_hien_tai);

-- dim_nhan_vien_ctxh
CREATE INDEX IF NOT EXISTS idx_dim_nv_ma_co_so
    ON public.btxh_dim_nhan_vien_ctxh (ma_co_so_hien_tai);

-- fact_hoat_dong_cham_soc
CREATE INDEX IF NOT EXISTS idx_fact_hdcs_ma_nguoi_thu_huong
    ON public.btxh_fact_hoat_dong_cham_soc (ma_nguoi_thu_huong);
CREATE INDEX IF NOT EXISTS idx_fact_hdcs_ma_co_so
    ON public.btxh_fact_hoat_dong_cham_soc (ma_co_so);

-- fact_ho_so_trung_tam
CREATE INDEX IF NOT EXISTS idx_fact_hstt_ma_nguoi_thu_huong
    ON public.btxh_fact_ho_so_trung_tam (ma_nguoi_thu_huong);
CREATE INDEX IF NOT EXISTS idx_fact_hstt_ma_co_so
    ON public.btxh_fact_ho_so_trung_tam (ma_co_so);

-- fact_gan_dich_vu
CREATE INDEX IF NOT EXISTS idx_fact_gdv_ma_nguoi_thu_huong
    ON public.btxh_fact_gan_dich_vu (ma_nguoi_thu_huong);
CREATE INDEX IF NOT EXISTS idx_fact_gdv_ma_co_so
    ON public.btxh_fact_gan_dich_vu (ma_co_so);

-- fact_nang_luc_co_so
CREATE INDEX IF NOT EXISTS idx_fact_nlcs_ngay_cap_nhat
    ON public.btxh_fact_nang_luc_co_so (ngay_cap_nhat);

-- fact_lich_su_cong_tac_xh
CREATE INDEX IF NOT EXISTS idx_fact_lsct_ma_nhan_vien_ctxh
    ON public.btxh_fact_lich_su_cong_tac_xh (ma_nhan_vien_ctxh);
CREATE INDEX IF NOT EXISTS idx_fact_lsct_ma_co_so
    ON public.btxh_fact_lich_su_cong_tac_xh (ma_co_so);

-- ---------------------------------------------------------------------------
-- NEW REFERENCE DIMENSIONS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.btxh_dim_dan_toc (
    id                              BIGINT          NOT NULL,
    ma_dan_toc                      VARCHAR(20)     NOT NULL,
    ten_dan_toc                     VARCHAR(100),
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_dan_toc  PRIMARY KEY (id),
    CONSTRAINT uq_btxh_dim_dan_toc  UNIQUE      (ma_dan_toc)
);

CREATE TABLE IF NOT EXISTS public.btxh_dim_vi_tri_cong_tac (
    id                              BIGINT          NOT NULL,
    ma_vi_tri                       VARCHAR(50)     NOT NULL,
    ten_vi_tri                      VARCHAR(255),
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_vi_tri_cong_tac  PRIMARY KEY (id),
    CONSTRAINT uq_btxh_dim_vi_tri_cong_tac  UNIQUE      (ma_vi_tri)
);

CREATE TABLE IF NOT EXISTS public.btxh_dim_loai_hop_dong (
    id                              BIGINT          NOT NULL,
    ma_loai_hop_dong                VARCHAR(50)     NOT NULL,
    ten_loai_hop_dong               VARCHAR(255),
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_loai_hop_dong    PRIMARY KEY (id),
    CONSTRAINT uq_btxh_dim_loai_hop_dong    UNIQUE      (ma_loai_hop_dong)
);

CREATE TABLE IF NOT EXISTS public.btxh_dim_loai_giay_to (
    id                              BIGINT          NOT NULL,
    ma_loai_giay_to                 VARCHAR(20)     NOT NULL,
    ten_loai_giay_to                VARCHAR(100),
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_dim_loai_giay_to     PRIMARY KEY (id),
    CONSTRAINT uq_btxh_dim_loai_giay_to     UNIQUE      (ma_loai_giay_to)
);

-- ---------------------------------------------------------------------------
-- NEW FACTS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong (
    id                              BIGINT          NOT NULL,
    ma_ho_so_trung_tam              VARCHAR(64)     NOT NULL,
    ma_nguoi_thu_huong              VARCHAR(64),
    ma_co_so                        VARCHAR(30),
    ma_nhom_doi_tuong_chinh         VARCHAR(50),
    ma_nhom_doi_tuong               VARCHAR(50)     NOT NULL,
    ma_chi_tiet_doi_tuong           VARCHAR(100),
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_fact_hstt_nhom   PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_hstt_nhom   UNIQUE      (ma_ho_so_trung_tam, ma_nhom_doi_tuong)
);

CREATE TABLE IF NOT EXISTS public.btxh_fact_muc_tieu_phuc_vu_co_so (
    id                              BIGINT          NOT NULL,
    ma_co_so                        VARCHAR(30)     NOT NULL,
    ma_dinh_danh_nguon_co_so        VARCHAR(64),
    ma_loai_trung_tam               VARCHAR(50),
    ma_muc_tieu_phuc_vu             VARCHAR(50)     NOT NULL,
    ngay_cap_nhat                   DATE,
    CONSTRAINT pk_btxh_fact_mtpv_co_so  PRIMARY KEY (id),
    CONSTRAINT uq_btxh_fact_mtpv_co_so  UNIQUE      (ma_co_so, ma_muc_tieu_phuc_vu)
);

-- ---------------------------------------------------------------------------
-- INDEXES – new tables
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_fact_hstt_nhom_ma_nguoi_thu_huong
    ON public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong (ma_nguoi_thu_huong);
CREATE INDEX IF NOT EXISTS idx_fact_hstt_nhom_ma_co_so
    ON public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong (ma_co_so);
CREATE INDEX IF NOT EXISTS idx_fact_hstt_nhom_ma_nhom_chinh
    ON public.btxh_fact_ho_so_trung_tam_nhom_doi_tuong (ma_nhom_doi_tuong_chinh);

CREATE INDEX IF NOT EXISTS idx_fact_mtpv_co_so_ma_loai_tt
    ON public.btxh_fact_muc_tieu_phuc_vu_co_so (ma_loai_trung_tam);

COMMIT;
