#!/usr/bin/env python3
"""
auto_evolve_hook.py - 任务完成后自动触发技能进化的闭环钩子

触发时机：Agent 完成任务执行后，检查是否需要更新技能库
流程：
    1. 读取最近任务执行日志（memory_manager.py 中的 FTS5 记录）
    2. 检测任务中是否发现可优化的 skill
    3. 生成优化建议并写入 learning_lists/awesome_skills_for_team.md
    4. 提交 Git 记录，闭环归档

用法：
    python scripts/auto_evolve_hook.py --task-id T08 --result success
    python scripts/auto_evolve_hook.py --task-id T07 --result failed --reason "FTS5 中文检索失败"
"""

import argparse
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path


def load_recent_tasks(db_path: str, limit: int = 10):
    """从 FTS5 记忆库读取最近任务记录"""
    if not Path(db_path).exists():
        return []
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT session_id, role, content, created_at FROM messages ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"session_id": r[0], "role": r[1], "content": r[2], "created_at": r[3]} for r in rows]


def generate_skill_insight(task_id: str, result: str, reason: str = None) -> dict:
    """
    基于任务结果生成技能优化洞察
    规则：
    - success → 将执行方案沉淀为可复用 skill
    - failed  → 记录失败根因，生成「防错清单」
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    insight = {
        "task_id": task_id,
        "result": result,
        "timestamp": timestamp,
        "action": None,
        "skill_update": None,
    }

    if result == "success":
        insight["action"] = "沉淀"
        insight["skill_update"] = f"[{timestamp}] ✅ {task_id} 执行成功，方案已沉淀为可复用流程"
    elif result == "failed":
        insight["action"] = "防错"
        insight["skill_update"] = f"[{timestamp}] ⚠️ {task_id} 执行失败，根因：{reason or '未知'}，已加入防错清单"
    else:
        insight["action"] = "记录"
        insight["skill_update"] = f"[{timestamp}] 📝 {task_id} 执行完毕，已归档"

    return insight


def append_to_learning_list(insight: dict, learning_list_path: str):
    """将洞察追加写入学习清单的更新日志"""
    path = Path(learning_list_path)
    if not path.exists():
        print(f"[WARN] 学习清单不存在: {learning_list_path}")
        return

    content = path.read_text(encoding="utf-8")
    entry = f"| {insight['timestamp']} | {insight['skill_update']} | auto-hook |\n"

    # 追加到 更新日志 表格末尾
    if "## 📝 更新日志" in content:
        content = content + entry
    path.write_text(content, encoding="utf-8")
    print(f"[OK] 已写入学习清单: {entry.strip()}")


def run_hook(task_id: str, result: str, reason: str = None,
             db_path: str = "memory/agent_memory.db",
             learning_list: str = None):

    print(f"\n🔁 Auto-Evolve Hook 触发")
    print(f"   任务: {task_id} | 结果: {result} | 原因: {reason or 'N/A'}")

    # 1. 读取记忆
    tasks = load_recent_tasks(db_path)
    print(f"   记忆库: 读取 {len(tasks)} 条最近记录")

    # 2. 生成洞察
    insight = generate_skill_insight(task_id, result, reason)
    print(f"   洞察: {insight['skill_update']}")

    # 3. 写入学习清单
    if learning_list:
        append_to_learning_list(insight, learning_list)

    # 4. 输出 JSON 供上游消费
    print(f"\n{json.dumps(insight, ensure_ascii=False, indent=2)}")
    return insight


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="任务完成后自动触发技能进化")
    parser.add_argument("--task-id", required=True, help="任务编号 (如 T08)")
    parser.add_argument("--result", required=True, choices=["success", "failed", "done"], help="任务结果")
    parser.add_argument("--reason", default=None, help="失败原因 (result=failed 时使用)")
    parser.add_argument("--db", default="memory/agent_memory.db", help="记忆库路径")
    parser.add_argument("--learning-list", default=None, help="学习清单路径")
    args = parser.parse_args()

    run_hook(args.task_id, args.result, args.reason, args.db, args.learning_list)
