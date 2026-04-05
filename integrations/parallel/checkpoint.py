"""
Checkpoint 机制 - 子进程中间状态抢救 + Brief 过大自动拆分

设计原则：
- 子进程定期把「当前进度」写入 checkpoint 文件（JSON 格式）
- 超时时主进程读取 checkpoint，提取 TaskBrief
- Brief 超过 token 阈值时，自动拆分为多个子 Brief
"""
import json
import os
import time
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, List, Dict
from pathlib import Path

# 默认 checkpoint 目录
DEFAULT_CHECKPOINT_DIR = Path("./checkpoints")

# Brief 大小阈值（字符数，约等于 token 数 * 4）
DEFAULT_BRIEF_MAX_CHARS = 4000  # 约 1000 tokens


@dataclass
class TaskBrief:
    """
    任务简报 - Worker 之间传递的最小上下文单元

    字段说明：
        task_id:      任务唯一 ID
        goal:         任务目标（一句话）
        context:      背景信息（≤ 100 字）
        progress:     已完成的步骤列表
        remaining:    剩余未完成的步骤列表
        artifacts:    已产出的中间结果（文件路径、数据等）
        metadata:     其他元数据
    """
    task_id: str
    goal: str
    context: str = ""
    progress: List[str] = field(default_factory=list)
    remaining: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "TaskBrief":
        return cls(**json.loads(data))

    def size(self) -> int:
        """返回 Brief 的字符数（用于判断是否需要拆分）"""
        return len(self.to_json())

    def is_oversized(self, max_chars: int = DEFAULT_BRIEF_MAX_CHARS) -> bool:
        return self.size() > max_chars

    def split(self, max_chars: int = DEFAULT_BRIEF_MAX_CHARS) -> List["TaskBrief"]:
        """
        Brief 过大时自动拆分为多个子 Brief。

        拆分策略：
        1. goal / context 保留在每个子 Brief 中（不可拆）
        2. remaining 步骤均分到各子 Brief
        3. artifacts 按步骤归属分配

        Returns:
            子 Brief 列表，每个都在 max_chars 以内
        """
        if not self.is_oversized(max_chars):
            return [self]

        if not self.remaining:
            # 没有剩余步骤，无法拆分，直接截断 context
            truncated = TaskBrief(
                task_id=self.task_id,
                goal=self.goal,
                context=self.context[:200] + "...[已截断]",
                progress=self.progress,
                remaining=self.remaining,
                artifacts=self.artifacts,
                metadata=self.metadata,
            )
            return [truncated]

        # 计算需要拆成几份
        base_size = len(json.dumps({
            "task_id": self.task_id,
            "goal": self.goal,
            "context": self.context,
            "progress": self.progress,
            "artifacts": {},
            "metadata": self.metadata,
        }, ensure_ascii=False))

        steps_size = len(json.dumps(self.remaining, ensure_ascii=False))
        n_splits = max(2, (base_size + steps_size) // max_chars + 1)

        # 均分 remaining 步骤
        chunk_size = max(1, len(self.remaining) // n_splits)
        sub_briefs = []

        for i in range(0, len(self.remaining), chunk_size):
            chunk_steps = self.remaining[i:i + chunk_size]
            sub_brief = TaskBrief(
                task_id=f"{self.task_id}-part{i // chunk_size + 1}",
                goal=self.goal,
                context=f"[第 {i // chunk_size + 1}/{n_splits} 部分] {self.context}",
                progress=self.progress.copy(),
                remaining=chunk_steps,
                artifacts=self.artifacts.copy(),
                metadata={**self.metadata, "split_index": i // chunk_size, "split_total": n_splits},
            )
            sub_briefs.append(sub_brief)

        return sub_briefs


class CheckpointWriter:
    """
    在子进程中使用，定期将当前进度写入 checkpoint 文件。

    用法（在 task_fn 内部）：
        writer = CheckpointWriter(task_id="T01", goal="实现 MCP 集成")
        writer.update_progress("已完成 Step 1：创建目录结构")
        writer.add_artifact("config_path", "/path/to/config.json")
        writer.set_remaining(["Step 2: 实现 client.py", "Step 3: 写文档"])
        writer.flush()  # 立即写入磁盘
    """

    def __init__(self, task_id: str, goal: str, context: str = "",
                 checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR):
        self.brief = TaskBrief(task_id=task_id, goal=goal, context=context)
        self._checkpoint_dir = Path(checkpoint_dir)
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._checkpoint_dir / f"{task_id}.json"
        self._lock = threading.Lock()

    def update_progress(self, step: str):
        """记录已完成的步骤"""
        with self._lock:
            self.brief.progress.append(f"[{time.strftime('%H:%M:%S')}] {step}")
            self._write()

    def set_remaining(self, steps: List[str]):
        """更新剩余步骤列表"""
        with self._lock:
            self.brief.remaining = steps
            self._write()

    def add_artifact(self, key: str, value: Any):
        """记录产出物（文件路径、数据等）"""
        with self._lock:
            self.brief.artifacts[key] = value
            self._write()

    def flush(self):
        """强制写入磁盘"""
        with self._lock:
            self._write()

    def _write(self):
        """写入 checkpoint 文件（原子写，防止读到半写状态）"""
        tmp_path = self._path.with_suffix(".tmp")
        tmp_path.write_text(self.brief.to_json(), encoding="utf-8")
        tmp_path.replace(self._path)  # 原子替换


class CheckpointReader:
    """
    在主进程中使用，读取子进程写入的 checkpoint。

    用法（在 AgentPool 超时处理中）：
        reader = CheckpointReader(task_id="T01")
        brief = reader.read()
        if brief:
            sub_briefs = brief.split()  # 如果过大，自动拆分
    """

    def __init__(self, task_id: str, checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR):
        self._path = Path(checkpoint_dir) / f"{task_id}.json"

    def read(self) -> Optional[TaskBrief]:
        """读取 checkpoint，不存在则返回 None"""
        if not self._path.exists():
            return None
        try:
            data = self._path.read_text(encoding="utf-8")
            return TaskBrief.from_json(data)
        except Exception:
            return None

    def cleanup(self):
        """清理 checkpoint 文件"""
        if self._path.exists():
            self._path.unlink()
