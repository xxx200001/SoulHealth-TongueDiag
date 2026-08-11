-- ============================================================
-- schema_module1.sql  模块① 体检报告指标量化入库
-- 与模块③ schema_module3.sql 同风格：user_confirmed 人审闸门 +
-- (user_id, test_date) 趋势折线索引 + audit_json 全程溯源
-- ============================================================

-- 体检报告元记录（每次上传一条）
CREATE TABLE IF NOT EXISTS lab_report (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    upload_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_type     VARCHAR(16) NOT NULL DEFAULT 'ocr',  -- ocr/manual/pdf
    image_path      VARCHAR(512),
    ocr_raw_text    TEXT,
    parse_version   VARCHAR(32),
    indicator_count INTEGER DEFAULT 0,
    abnormal_count  INTEGER DEFAULT 0,
    liver_grade     TINYINT DEFAULT 0,    -- 全报告肝功最高等级(便于风控快查)
    renal_grade     TINYINT DEFAULT 0,    -- 全报告肾功最高等级
    audit_json      TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_lr_user ON lab_report (user_id, upload_at);

-- 单项指标记录（每次报告每个指标一条）
CREATE TABLE IF NOT EXISTS lab_indicator (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       INTEGER NOT NULL REFERENCES lab_report(id),
    user_id         INTEGER NOT NULL,
    test_date       DATE NOT NULL,        -- 体检日期(用于趋势图)
    name            VARCHAR(32) NOT NULL,  -- 标准化名称(ALT/AST/TG...)
    name_raw        VARCHAR(64),           -- OCR原始名称
    value           REAL NOT NULL,
    unit            VARCHAR(16),
    ref_low         REAL,
    ref_high        REAL,
    direction       VARCHAR(8),            -- normal/high/low
    grade           TINYINT DEFAULT 0,     -- 0-3
    grade_label     VARCHAR(16),
    category        VARCHAR(16),           -- 肝功能/肾功能/血脂/血糖/...
    audit_json      TEXT,
    user_confirmed  TINYINT NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_li_trend ON lab_indicator (user_id, name, test_date);
CREATE INDEX IF NOT EXISTS idx_li_report ON lab_indicator (report_id);
CREATE INDEX IF NOT EXISTS idx_li_abnormal ON lab_indicator (user_id, grade) WHERE grade > 0;
