#!/usr/bin/env python3
"""
flow_runtime.py - ClawFlow 核心运行时封装
基于 OpenClaw ClawFlow Skill 设计理念
https://docs.openclaw.ai/skills/clawflow

核心能力：
1. 创建 Flow（任务身份标识 + owner 绑定）
2. 运行子任务（每步带状态快照）
3. 等待/恢复（解决任务断层问题）
4. 持久化输出（FlowOutput 存入 SQLite）
5. 熔断与失败处理
"""

import json
import sqlite3
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class FlowState(Enum):
    RUNNING  = "running"
    WAITING  = "waiting"
    BLOCKED  = "blocked"
    FINISHED = "finished"
    FAILED   = "failed"
    CANCELLED = "cancelled"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS flows (
    flow_id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    owner_session TEXT,
    state TEXT DEFAULT 'running',
    current_step TEXT,
    created_at REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS flow_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    created_at REAL DEFAULT (unixepoch('now')),
    FOREIGN KEY (flow_id) REFERENCES flows(flow_id)
);

CREATE TABLE IF NOT EXISTS flow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    state TEXT DEFAULT 'running',
    started_at REAL,
    finished_at REAL,
    result TEXT,
    FOREIGN KEY (flow_id) REFERENCES flows(flow_id)
);
"""


class FlowRuntime:
    """
    ClawFlow 核心运行时
    负责 flow 身份 / 等待状态 / 持久化输出 / 完成与失败
    业务逻辑由调用方负责，runtime 只管状态
    """

    def __init__(self, db_path: str = "memory/flows.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()

    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── 1. 创建 Flow ────────────────────────────────────────────────────
    def create_flow(self, goal: str, owner_session: str = None) -> str:
        flow_id = str(uuid.uuid4())[:8]
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO flows (flow_id, goal, owner_session, state, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (flow_id, goal, owner_session, FlowState.RUNNING.value, now, now)
            )
        print(f"[FLOW] ✅ 创建 flow_id={flow_id} goal={goal!r}")
        return flow_id

    # ── 2. 记录步骤 ─────────────────────────────────────────────────────
    def run_step(self, flow_id: str, step_name: str) -> int:
        now = time.time()
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO flow_steps (flow_id, step_name, state, started_at) VALUES (?,?,?,?)",
                (flow_id, step_name, "running", now)
            )
            conn.execute(
                "UPDATE flows SET current_step=?, updated_at=? WHERE flow_id=?",
                (step_name, now, flow_id)
            )
            step_id = cursor.lastrowid
        print(f"[FLOW] 🔄 step={step_name} started (flow={flow_id})")
        return step_id

    def finish_step(self, flow_id: str, step_id: int, result: str = None):
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "UPDATE flow_steps SET state='finished', finished_at=?, result=? WHERE id=?",
                (now, result, step_id)
            )
        print(f"[FLOW] ✅ step_id={step_id} finished")

    # ── 3. 等待与恢复 ───────────────────────────────────────────────────
    def set_waiting(self, flow_id: str, reason: str = None):
        with self._conn() as conn:
            conn.execute(
                "UPDATE flows SET state=?, updated_at=? WHERE flow_id=?",
                (FlowState.WAITING.value, time.time(), flow_id)
            )
        print(f"[FLOW] ⏸️  flow={flow_id} 等待中 reason={reason}")

    def resume(self, flow_id: str, next_step: str = None):
        with self._conn() as conn:
            conn.execute(
                "UPDATE flows SET state=?, current_step=?, updated_at=? WHERE flow_id=?",
                (FlowState.RUNNING.value, next_step, time.time(), flow_id)
            )
        print(f"[FLOW] ▶️  flow={flow_id} 已恢复 next_step={next_step}")

    # ── 4. 持久化输出 ───────────────────────────────────────────────────
    def set_output(self, flow_id: str, key: str, value: Any):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO flow_outputs (flow_id, key, value) VALUES (?,?,?)",
                (flow_id, key, json.dumps(value, ensure_ascii=False))
            )
        print(f"[FLOW] 💾 output saved key={key}")

    def get_output(self, flow_id: str, key: str) -> Any:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM flow_outputs WHERE flow_id=? AND key=? ORDER BY id DESC LIMIT 1",
                (flow_id, key)
            ).fetchone()
        return json.loads(row["value"]) if row else None

    # ── 5. 完成与失败 ───────────────────────────────────────────────────
    def finish_flow(self, flow_id: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE flows SET state=?, updated_at=? WHERE flow_id=?",
                (FlowState.FINISHED.value, time.time(), flow_id)
            )
        print(f"[FLOW] 🎉 flow={flow_id} 已完成")

    def fail_flow(self, flow_id: str, reason: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE flows SET state=?, updated_at=? WHERE flow_id=?",
                (FlowState.FAILED.value, time.time(), flow_id)
            )
        print(f"[FLOW] ❌ flow={flow_id} 失败 reason={reason}")

    # ── 6. 查询状态 ─────────────────────────────────────────────────────
    def get_flow(self, flow_id: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM flows WHERE flow_id=?", (flow_id,)
            ).fetchone()
        return dict(row) if row else {}

    def list_active_flows(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT flow_id, goal, state, current_step FROM flows WHERE state IN ('running','waiting')"
            ).fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        rt = FlowRuntime(os.path.join(d, "memory", "flows.db"))

        # 模拟多步骤任务
        fid = rt.create_flow("分析 Hermes Agent 并集成到 smart-agent-template", owner_session="zuzhang")

        s1 = rt.run_step(fid, "clone_repo")
        rt.finish_step(fid, s1, result="克隆成功")

        s2 = rt.run_step(fid, "analyze_core")
        rt.set_output(fid, "key_modules", ["trajectory_compressor", "fts5_memory", "evolution_core"])
        rt.finish_step(fid, s2, result="分析完成，发现3个核心模块")

        s3 = rt.run_step(fid, "integrate")
        rt.set_waiting(fid, reason="等待 git push 确认")
        rt.resume(fid, next_step="verify")

        rt.set_output(fid, "commits", ["8105202", "56460f9", "a397b67"])
        rt.finish_step(fid, s3, result="集成完成，已推送")

        rt.finish_flow(fid)

        # 验证
        flow = rt.get_flow(fid)
        assert flow["state"] == "finished", f"Flow state 错误: {flow['state']}"
        modules = rt.get_output(fid, "key_modules")
        assert len(modules) == 3, "Output 读取失败"
        active = rt.list_active_flows()
        assert len(active) == 0, "完成的 flow 不应出现在活跃列表"

        print("\n✅ 所有测试通过")
        print(f"   flow_id={fid} state={flow['state']}")
        print(f"   key_modules={modules}")
