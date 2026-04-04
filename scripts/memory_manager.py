#!/usr/bin/env python3
"""
Memory Manager - FTS5 全文检索记忆系统
移植自 NousResearch/hermes-agent hermes_state.py
适配 smart-agent-template 架构

核心能力：
1. SQLite WAL 模式存储对话记录
2. FTS5 全文索引，支持跨会话检索
3. 触发器自动同步，写入即索引
"""

import json
import sqlite3
import threading
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    source TEXT DEFAULT 'agent',
    started_at REAL,
    last_active REAL,
    model TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    created_at REAL DEFAULT (unixepoch('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id,
    tokenize="trigram"
);

CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
"""

class MemoryManager:
    """
    SQLite + FTS5 记忆管理器
    线程安全，WAL 模式支持多并发读写
    """

    def __init__(self, db_path: str = "memory/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info(f"Memory DB initialized: {self.db_path}")

    def create_session(self, session_id: str, title: str = None, source: str = "agent", model: str = None):
        conn = self._get_conn()
        now = time.time()
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, title, source, started_at, last_active, model) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, title, source, now, now, model)
        )
        conn.commit()

    def add_message(self, session_id: str, role: str, content: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.execute(
            "UPDATE sessions SET last_active = ? WHERE id = ?",
            (time.time(), session_id)
        )
        conn.commit()

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """FTS5 全文检索，返回相关消息列表"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT m.session_id, m.role, m.content, m.created_at,
                   rank
            FROM messages_fts
            JOIN messages m ON messages_fts.rowid = m.id
            WHERE messages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """获取某个 session 的完整对话记录"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


if __name__ == "__main__":
    # 快速自测
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "memory", "test.db")
        mm = MemoryManager(db_path)

        mm.create_session("s001", title="iOS 开发任务", source="ethon")
        mm.add_message("s001", "user", "请帮我实现 Tiqmo 的登录页面")
        mm.add_message("s001", "assistant", "好的，我将使用 ObjC + MVC 架构实现登录页面")
        mm.add_message("s001", "user", "需要支持手机号验证码登录")
        mm.add_message("s001", "assistant", "已实现手机号验证码登录，代码已提交到 main 分支")

        mm.create_session("s002", title="UI 设计评审", source="xiaoming")
        mm.add_message("s002", "user", "请检查登录页面的 WCAG 无障碍规范")
        mm.add_message("s002", "assistant", "登录按钮对比度不足，已修复至 AA 标准")

        # FTS5 检索测试
        results = mm.search("登录 验证码")
        assert len(results) > 0, "FTS5 检索失败"
        assert any("验证码" in r["content"] for r in results), "未检索到相关内容"

        results2 = mm.search("WCAG 无障碍")
        assert len(results2) > 0, "WCAG 检索失败"

        print("✅ 所有测试通过")
        print(f"   - 检索 '登录 验证码': {len(results)} 条结果")
        print(f"   - 检索 'WCAG 无障碍': {len(results2)} 条结果")
        mm.close()
