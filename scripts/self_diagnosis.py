#!/usr/bin/env python3
"""
self_diagnosis.py - Agent 自我诊断工具

当 Agent 执行失败时，自动分析根因并生成修复建议。
联动 memory_manager.py 的 FTS5 记忆库，检索历史相似失败案例。

用法：
    python scripts/self_diagnosis.py --task-id T07 --error "FTS5 检索失败" --exit-code 1
    python scripts/self_diagnosis.py --task-id T06 --error "git push failed" --exit-code 128
"""

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# 已知错误模式库（基于今日实际踩坑积累）
ERROR_PATTERNS = [
    {
        "pattern": r"exit.*128|push.*failed|fatal.*unable to access",
        "root_cause": "Git 认证失败或远端分支不存在",
        "fix": "检查 git remote -v，确认 push URL 正确；检查 gh auth status",
        "learned_from": "T06-B push 失败"
    },
    {
        "pattern": r"AssertionError|FTS5|fts.*fail",
        "root_cause": "SQLite FTS5 中文检索失败，默认 tokenizer 不支持中文",
        "fix": "使用 tokenize=\"trigram\" 替代默认 unicode61",
        "learned_from": "T07 FTS5 检索失败"
    },
    {
        "pattern": r"exec denied|allowlist miss",
        "root_cause": "exec 安全策略为 allowlist 模式，命令被拦截",
        "fix": "执行 openclaw config set tools.exec.security full，重启 Gateway",
        "learned_from": "今日 allowlist 拦截 gh 命令"
    },
    {
        "pattern": r"no changes.*commit|nothing to commit",
        "root_cause": "文件已存在于仓库，无需重复提交",
        "fix": "先用 diff 确认文件是否已是最新；若是则跳过提交步骤",
        "learned_from": "T08-A 重复提交失败"
    },
    {
        "pattern": r"ModuleNotFoundError|ImportError",
        "root_cause": "Python 依赖缺失",
        "fix": "先执行 pip install -r requirements.txt；检查 venv 是否激活",
        "learned_from": "通用 Python 错误"
    },
    {
        "pattern": r"gateway.*not loaded|service.*not.*installed",
        "root_cause": "OpenClaw Gateway 未以系统服务形式启动",
        "fix": "执行 openclaw gateway 手动启动；或 openclaw gateway install 安装为服务",
        "learned_from": "今日 Gateway 启动问题"
    },
]


def match_error(error_msg: str) -> list:
    """匹配已知错误模式，返回所有命中项"""
    matches = []
    for p in ERROR_PATTERNS:
        if re.search(p["pattern"], error_msg, re.IGNORECASE):
            matches.append(p)
    return matches


def search_memory(db_path: str, query: str, limit: int = 3) -> list:
    """从 FTS5 记忆库检索历史相似案例"""
    if not Path(db_path).exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        # trigram FTS5 检索
        rows = conn.execute(
            "SELECT session_id, content FROM messages_fts WHERE messages_fts MATCH ? LIMIT ?",
            (query, limit)
        ).fetchall()
        conn.close()
        return [{"session_id": r[0], "content": r[1][:200]} for r in rows]
    except Exception:
        return []


def diagnose(task_id: str, error: str, exit_code: int,
             db_path: str = "memory/agent_memory.db") -> dict:
    """执行诊断，返回结构化报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. 模式匹配
    known_matches = match_error(error)

    # 2. 记忆库检索
    memory_hits = search_memory(db_path, error[:50])

    # 3. 生成报告
    report = {
        "task_id": task_id,
        "timestamp": timestamp,
        "error": error,
        "exit_code": exit_code,
        "diagnosis": {
            "known_pattern_hits": len(known_matches),
            "memory_hits": len(memory_hits),
            "root_cause": known_matches[0]["root_cause"] if known_matches else "未知，需人工分析",
            "fix": known_matches[0]["fix"] if known_matches else "建议查看完整错误日志",
            "learned_from": known_matches[0]["learned_from"] if known_matches else None,
        },
        "next_action": "自动修复" if known_matches else "⚠️ 需要人工介入",
        "memory_context": memory_hits[:2] if memory_hits else []
    }

    return report


def print_report(report: dict):
    print(f"\n🔍 自我诊断报告")
    print(f"   任务：{report['task_id']} | 时间：{report['timestamp']}")
    print(f"   错误：{report['error'][:80]}")
    print(f"   退出码：{report['exit_code']}")
    print(f"\n   📌 根因：{report['diagnosis']['root_cause']}")
    print(f"   🔧 修复方案：{report['diagnosis']['fix']}")
    if report['diagnosis']['learned_from']:
        print(f"   📚 来源：{report['diagnosis']['learned_from']}")
    print(f"\n   🚀 下一步：{report['next_action']}")
    if report['memory_context']:
        print(f"   💾 记忆库命中 {len(report['memory_context'])} 条相关记录")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent 自我诊断工具")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--error", required=True)
    parser.add_argument("--exit-code", type=int, default=1)
    parser.add_argument("--db", default="memory/agent_memory.db")
    args = parser.parse_args()

    report = diagnose(args.task_id, args.error, args.exit_code, args.db)
    print_report(report)
    print(f"\n{json.dumps(report, ensure_ascii=False, indent=2)}")
