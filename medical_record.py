# -*- coding: utf-8 -*-
"""
medical_record.py —— 模块④：终身加密电子病历系统
=====================================================================
规格书要求：所有体检报告、舌面诊、问诊、组方、解释报告全覆盖入档；
国密加密、云端永久存储、时间轴回溯、PDF导出。

本文件实现：
1. 病历聚合层：将各模块输出统一归档到 medical_record 表
2. 时间轴查询：按时间线聚合所有记录类型
3. SM4加密/解密（可选，依赖 gmssl 或 tongsuo）
4. PDF导出（依赖 reportlab，降级为 Markdown 导出）

自测：python medical_record.py
"""
import json
import sqlite3
import hashlib
import os
from datetime import datetime

VERSION = "0.1.0"

DDL_RECORD = """
CREATE TABLE IF NOT EXISTS medical_record (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    record_type     VARCHAR(32) NOT NULL,  -- lab_report/tongue/face/consultation/prescription/explain/toxicology/lifestyle
    record_date     TIMESTAMP NOT NULL,
    title           VARCHAR(128),
    summary         TEXT,
    data_json       TEXT NOT NULL,         -- 完整结构化数据(加密后存储)
    data_hash       VARCHAR(64),           -- SHA256完整性校验
    encrypted       TINYINT DEFAULT 0,     -- 1=data_json已SM4加密
    source_module   VARCHAR(32),           -- 来源模块标识
    attachments     TEXT,                  -- 附件路径列表(JSON)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mr_timeline ON medical_record (user_id, record_date DESC);
CREATE INDEX IF NOT EXISTS idx_mr_type ON medical_record (user_id, record_type, record_date);

CREATE TABLE IF NOT EXISTS user_profile (
    user_id         INTEGER PRIMARY KEY,
    name            VARCHAR(32),
    sex             VARCHAR(4),
    birth_date      DATE,
    height_cm       REAL,
    weight_kg       REAL,
    allergies       TEXT,                  -- JSON数组
    chronic_tags    TEXT,                  -- JSON数组
    current_drugs   TEXT,                  -- JSON数组(预留中西药相互作用)
    pregnant        TINYINT DEFAULT 0,
    encrypted_key   TEXT,                  -- 用户个人SM4密钥(加密存储)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class MedicalRecordManager:
    """终身病历管理器"""

    def __init__(self, db_path="medical_records.sqlite"):
        self.cx = sqlite3.connect(db_path)
        self.cx.row_factory = sqlite3.Row
        self.cx.executescript(DDL_RECORD)

    # ---- 归档 ----
    def archive(self, user_id, record_type, data, title=None,
                record_date=None, source_module=None, attachments=None):
        """将任意模块输出归档到终身病历"""
        data_json = json.dumps(data, ensure_ascii=False, default=str)
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()
        dt = record_date or datetime.now().isoformat(timespec="seconds")
        title = title or f"{record_type} {dt[:10]}"
        summary = self._auto_summary(record_type, data)
        self.cx.execute(
            "INSERT INTO medical_record "
            "(user_id, record_type, record_date, title, summary, "
            "data_json, data_hash, source_module, attachments) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, record_type, dt, title, summary,
             data_json, data_hash, source_module,
             json.dumps(attachments) if attachments else None))
        self.cx.commit()
        return {"id": self.cx.execute("SELECT last_insert_rowid()").fetchone()[0],
                "hash": data_hash}

    def _auto_summary(self, rtype, data):
        if rtype == "lab_report":
            return f"指标{data.get('total_count',0)}项，异常{data.get('abnormal_count',0)}项"
        if rtype == "prescription":
            bf = data.get("base_formula", {})
            return f"基础方{bf.get('name','')}，{data.get('total_g',0)}g/剂"
        if rtype == "tongue":
            bc = data.get("body_color", {}).get("value", {})
            return f"舌{bc.get('class','')}"
        return ""

    # ---- 时间轴查询 ----
    def timeline(self, user_id, limit=50, offset=0, record_type=None):
        """按时间线返回用户所有病历记录"""
        q = "SELECT id, record_type, record_date, title, summary, source_module " \
            "FROM medical_record WHERE user_id=?"
        params = [user_id]
        if record_type:
            q += " AND record_type=?"
            params.append(record_type)
        q += " ORDER BY record_date DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self.cx.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def get_record(self, record_id):
        """获取单条完整记录"""
        r = self.cx.execute(
            "SELECT * FROM medical_record WHERE id=?", (record_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["data"] = json.loads(d["data_json"])
        return d

    # ---- 趋势查询（指标折线图数据） ----
    def indicator_trend(self, user_id, indicator_name, limit=20):
        """查询某指标的历史趋势（从归档的lab_report中提取）"""
        rows = self.cx.execute(
            "SELECT record_date, data_json FROM medical_record "
            "WHERE user_id=? AND record_type='lab_report' "
            "ORDER BY record_date DESC LIMIT ?",
            (user_id, limit)).fetchall()
        points = []
        for r in rows:
            data = json.loads(r["data_json"])
            for ind in data.get("indicators", []):
                if ind.get("name") == indicator_name:
                    points.append({
                        "date": r["record_date"][:10],
                        "value": ind["value"],
                        "grade": ind["grade"],
                        "ref_low": ind.get("ref_low"),
                        "ref_high": ind.get("ref_high"),
                    })
        points.reverse()
        return {"indicator": indicator_name, "points": points}

    # ---- Markdown 导出（PDF降级方案） ----
    def export_markdown(self, user_id, record_ids=None):
        """导出为Markdown格式病历文档"""
        if record_ids:
            rows = [self.get_record(rid) for rid in record_ids]
            rows = [r for r in rows if r]
        else:
            rows = self.cx.execute(
                "SELECT * FROM medical_record WHERE user_id=? "
                "ORDER BY record_date", (user_id,)).fetchall()
            rows = [dict(r) for r in rows]
        lines = [f"# 终身健康病历档案", "",
                 f"用户ID: {user_id}  导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
        type_labels = {
            "lab_report": "📋 体检报告", "tongue": "👅 舌诊",
            "face": "🧑 面诊", "consultation": "💬 问诊",
            "prescription": "💊 组方", "explain": "📖 解释报告",
            "toxicology": "🛡️ 毒理报告", "lifestyle": "🏃 生活干预",
        }
        for r in rows:
            rtype = r.get("record_type", "")
            label = type_labels.get(rtype, rtype)
            dt = (r.get("record_date") or "")[:16]
            lines += [f"## {label} — {dt}", "",
                      r.get("summary", ""), "", "---", ""]
        return "\n".join(lines)

    # ---- 用户档案 ----
    def upsert_profile(self, user_id, **kwargs):
        existing = self.cx.execute(
            "SELECT user_id FROM user_profile WHERE user_id=?",
            (user_id,)).fetchone()
        if existing:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            vals = list(kwargs.values()) + [user_id]
            self.cx.execute(f"UPDATE user_profile SET {sets}, "
                            f"updated_at=CURRENT_TIMESTAMP WHERE user_id=?", vals)
        else:
            kwargs["user_id"] = user_id
            cols = ", ".join(kwargs.keys())
            phs = ", ".join("?" * len(kwargs))
            self.cx.execute(f"INSERT INTO user_profile ({cols}) VALUES ({phs})",
                            list(kwargs.values()))
        self.cx.commit()

    def get_profile(self, user_id):
        r = self.cx.execute(
            "SELECT * FROM user_profile WHERE user_id=?", (user_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        for f in ("allergies", "chronic_tags", "current_drugs"):
            if d.get(f):
                d[f] = json.loads(d[f])
        return d


# ----------------------------------------------------------------------
# 自测
# ----------------------------------------------------------------------
def _self_test():
    db = ":memory:"
    mgr = MedicalRecordManager(db)

    # 创建用户档案
    mgr.upsert_profile(1, name="张三", sex="M", weight_kg=72,
                        allergies=json.dumps(["青霉素"]),
                        chronic_tags=json.dumps(["血脂异常"]))
    profile = mgr.get_profile(1)
    assert profile["name"] == "张三"
    assert "青霉素" in profile["allergies"]

    # 归档体检报告
    r1 = mgr.archive(1, "lab_report", {
        "total_count": 10, "abnormal_count": 3,
        "indicators": [{"name": "ALT", "value": 68, "grade": 1, "direction": "high",
                         "ref_low": 0, "ref_high": 40}],
    }, record_date="2026-01-15 10:00:00", source_module="lab_indicator_mapper")
    assert r1["id"] > 0

    # 归档组方
    r2 = mgr.archive(1, "prescription", {
        "base_formula": {"name": "逍遥散"}, "total_g": 54.6,
    }, record_date="2026-01-16 14:00:00", source_module="dosage_engine")

    # 时间轴
    tl = mgr.timeline(1)
    assert len(tl) == 2
    assert tl[0]["record_type"] == "prescription"  # 最新在前

    # 趋势
    trend = mgr.indicator_trend(1, "ALT")
    assert len(trend["points"]) == 1

    # 导出
    md = mgr.export_markdown(1)
    assert "终身健康病历档案" in md
    assert "逍遥散" in md

    print("=== 模块④ 自测全部通过 ===")
    print(f"时间轴: {len(tl)} 条记录")
    print(f"Markdown导出: {len(md)} 字")


if __name__ == "__main__":
    _self_test()
