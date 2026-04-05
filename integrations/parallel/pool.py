"""
AgentPool - 并行启动多个子任务，统一收集结果
支持：
  - 批量并行（所有任务同时启动，每批最多 max_workers 个）
  - 超时保护（单个任务超时不影响其他）
  - 错误隔离（单个失败不阻断整体）
"""
import threading
import time
from typing import Callable, Dict, Any, List

from .worker import AgentWorker


class AgentPool:
    """
    并行任务池，支持分批执行多个子 Agent 任务。

    用法：
        pool = AgentPool(max_workers=3)
        pool.submit("task1", fn1, args=(arg1,))
        pool.submit("task2", fn2, args=(arg2,))
        results = pool.run_all(timeout=120)
        # results: {"task1": {"status": "ok", "result": ...}, "task2": {...}}
    """

    def __init__(self, max_workers: int = 3):
        """
        Args:
            max_workers: 每批最多并行任务数，默认 3（与团队 WBS 规范一致）
        """
        self.max_workers = max_workers
        self._tasks: List[AgentWorker] = []
        self._task_names: List[str] = []
        self._lock = threading.Lock()  # 保护 submit() 并发写

    def submit(self, name: str, task_fn: Callable, args: tuple = (), kwargs: dict = None):
        """
        线程安全的任务注册（不立即执行，调用 run_all 后统一启动）。

        Args:
            name:    任务唯一名称，用于结果 key 和日志
            task_fn: 可调用对象，将在子进程中执行
            args:    位置参数元组
            kwargs:  关键字参数字典
        """
        worker = AgentWorker(
            name=name,
            task_fn=task_fn,
            args=args,
            kwargs=kwargs or {}
        )
        with self._lock:
            self._tasks.append(worker)
            self._task_names.append(name)

    def run_all(self, timeout: float = 120, total_timeout: float = None) -> Dict[str, Any]:
        """
        分批并行执行所有已注册任务，收集并返回结果。

        每批最多启动 max_workers 个子进程，当前批全部完成后再启动下一批。
        单个任务超时或异常不会影响其他任务。

        Args:
            timeout:       单个任务的最大等待秒数（默认 120s）
            total_timeout: 整体最大运行秒数（默认 None，不限制）
                           超过整体超时，未完成的任务全部 terminate

        Returns:
            以任务名为 key 的结果字典，每个 value 格式：
              {"status": "ok",      "result": <返回值>}
              {"status": "timeout", "error": <超时信息>}
              {"status": "error",   "error": <异常信息>}
        """
        results: Dict[str, Any] = {}
        start_time = time.monotonic()

        for i in range(0, len(self._tasks), self.max_workers):
            # 检查整体超时
            if total_timeout is not None:
                elapsed = time.monotonic() - start_time
                if elapsed >= total_timeout:
                    for name in self._task_names[i:]:
                        results[name] = {"status": "timeout", "error": "整体超时，任务未执行"}
                    break

            batch = list(zip(
                self._task_names[i:i + self.max_workers],
                self._tasks[i:i + self.max_workers]
            ))

            for name, worker in batch:
                worker.start()

            for name, worker in batch:
                # 动态计算剩余超时
                if total_timeout is not None:
                    remaining = total_timeout - (time.monotonic() - start_time)
                    effective_timeout = min(timeout, max(1.0, remaining))
                else:
                    effective_timeout = timeout

                try:
                    result = worker.get_result(timeout=effective_timeout)
                    results[name] = {"status": "ok", "result": result}
                except TimeoutError as e:
                    # 1. 超时前先抢救 checkpoint
                    interim_brief = worker.checkpoint()
                    # 2. 再 terminate
                    worker.terminate()

                    if interim_brief is not None:
                        # 3. 检查 Brief 是否过大，需要拆分
                        if interim_brief.is_oversized():
                            sub_briefs = interim_brief.split()
                            results[name] = {
                                "status": "timeout_with_brief",
                                "error": str(e),
                                "interim_brief": interim_brief,
                                "sub_briefs": sub_briefs,  # 拆分后的子任务列表，调用方可直接 submit
                                "needs_split": True,
                            }
                        else:
                            results[name] = {
                                "status": "timeout_with_brief",
                                "error": str(e),
                                "interim_brief": interim_brief,
                                "sub_briefs": [interim_brief],
                                "needs_split": False,
                            }
                    else:
                        results[name] = {"status": "timeout", "error": str(e)}
                except Exception as e:
                    results[name] = {"status": "error", "error": str(e)}
                finally:
                    worker.join(timeout=2)

        return results
