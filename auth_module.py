# -*- coding: utf-8 -*-
"""
auth_module.py —— JWT 认证模块
=====================================================================
提供用户注册、登录、JWT 签发/校验、路由保护。
用户存储在 SQLite users.db 中，密码用 bcrypt 哈希。

API:
  POST /api/v1/register  { phone, password, nickname? }
  POST /api/v1/login     { phone, password }
  GET  /api/v1/me        (需 Authorization: Bearer <token>)
  POST /api/v1/save_record   (需登录, 保存病历到服务器)
  GET  /api/v1/my_records    (需登录, 拉取该用户所有病历)
"""

import os
import sqlite3
import uuid
import time
import json
from datetime import datetime

import bcrypt
import jwt

# ---- 配置 ----
JWT_SECRET = os.environ.get("JWT_SECRET", "soulhealth_2026_secret_key_!@#")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 7 * 24 * 3600  # 7天

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


# ---- 数据库初始化 ----
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        phone TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nickname TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        last_login TEXT
    );
    CREATE TABLE IF NOT EXISTS medical_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        type TEXT NOT NULL,
        summary TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_records_user ON medical_records(user_id);
    """)
    conn.commit()
    conn.close()


init_db()


# ---- 密码工具 ----
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ---- JWT 工具 ----
def create_token(user_id: str, phone: str, nickname: str = "") -> str:
    payload = {
        "sub": user_id,
        "phone": phone,
        "nickname": nickname,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码JWT，失败抛异常"""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ---- 用户操作 ----
def register_user(phone: str, password: str, nickname: str = "") -> dict:
    """注册新用户，返回 {user, token}"""
    if not phone or len(phone) < 5:
        raise ValueError("手机号格式不正确")
    if not password or len(password) < 4:
        raise ValueError("密码至少4位")

    conn = _get_conn()
    # 检查是否已注册
    existing = conn.execute("SELECT id FROM users WHERE phone=?", (phone,)).fetchone()
    if existing:
        conn.close()
        raise ValueError("该手机号已注册，请直接登录")

    user_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat() + "Z"
    pw_hash = hash_password(password)

    conn.execute(
        "INSERT INTO users (id, phone, password_hash, nickname, created_at) VALUES (?,?,?,?,?)",
        (user_id, phone, pw_hash, nickname or f"用户{phone[-4:]}", now)
    )
    conn.commit()
    conn.close()

    token = create_token(user_id, phone, nickname)
    return {
        "user": {"id": user_id, "phone": phone, "nickname": nickname or f"用户{phone[-4:]}"},
        "token": token,
    }


def login_user(phone: str, password: str) -> dict:
    """登录，返回 {user, token}"""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
    if not row:
        conn.close()
        raise ValueError("该手机号未注册")

    if not verify_password(password, row["password_hash"]):
        conn.close()
        raise ValueError("密码错误")

    # 更新登录时间
    now = datetime.utcnow().isoformat() + "Z"
    conn.execute("UPDATE users SET last_login=? WHERE id=?", (now, row["id"]))
    conn.commit()
    conn.close()

    token = create_token(row["id"], row["phone"], row["nickname"])
    return {
        "user": {"id": row["id"], "phone": row["phone"], "nickname": row["nickname"]},
        "token": token,
    }


def get_user_by_token(token: str) -> dict:
    """通过JWT获取用户信息"""
    payload = decode_token(token)
    return {"id": payload["sub"], "phone": payload["phone"], "nickname": payload.get("nickname", "")}


# ---- 病历存储 ----
def save_record(user_id: str, record_type: str, summary: str, data: dict) -> dict:
    """保存一条病历记录"""
    conn = _get_conn()
    record_id = str(uuid.uuid4())[:12]
    now = datetime.utcnow().isoformat() + "Z"
    conn.execute(
        "INSERT INTO medical_records (id, user_id, type, summary, data, created_at) VALUES (?,?,?,?,?,?)",
        (record_id, user_id, record_type, summary, json.dumps(data, ensure_ascii=False), now)
    )
    conn.commit()
    conn.close()
    return {"id": record_id, "created_at": now}


def get_records(user_id: str) -> list:
    """获取该用户的所有病历"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM medical_records WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "type": r["type"],
            "summary": r["summary"],
            "data": json.loads(r["data"]),
            "date": r["created_at"],
        })
    return result


def delete_record(user_id: str, record_id: str) -> bool:
    """删除一条病历（仅限本人）"""
    conn = _get_conn()
    cursor = conn.execute(
        "DELETE FROM medical_records WHERE id=? AND user_id=?",
        (record_id, user_id)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
