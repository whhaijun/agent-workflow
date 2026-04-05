"""
并行 Worker - 在独立子进程中运行子任务
使用 Python 标准库 multiprocessing + Queue 实现
"""
import multiprocessing
import queue
import traceback
from pathlib import Path
from typing import Callable, Any, Optional

from .checkpoint import DEFAULT_CHECKPOINT_DIR, CheckpointReader


class AgentWorker:
    """
    在独立子进程中运行一个 Agent 子任务。

    用法：
        worker = AgentWorker(name="ethon", task_fn=my_task, args=(arg1,))
        worker.start()
        result = worker.get_result(timeout=60)
        worker.join()
    """

    def __init__(self, name: str, task_fn: Callable, args: tuple = (), kwargs: dict = None):
        self.name = name
        self._result_queue = multiprocessing.Queue()
        self._process = multiprocessing.Process(
            target=self._run,
            args=(task_fn, args, kwargs or {}, self._result_queue),
            name=f"agent-worker-{name}"
        )
        # checkpoint 路径（子进程写，主进程读）
        self.checkpoint_path = DEFAULT_CHECKPOINT_DIR / f"{name}.json"
        self._checkpoint_reader = CheckpointReader(task_id=name)

    @staticmethod
    def _run(task_fn: Callable, args: tuple, kwargs: dict, result_queue: multiprocessing.Queue):
        """子进程入口：执行任务函数并将结果放入队列"""
        try:
            result = task_fn(*args, **kwargs)
            result_queue.put({"status": "ok", "result": result})
        except Exception as e:
            # 捕获所有异常，序列化后传回主进程
            result_queue.put({
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    def start(self):
        """启动子进程"""
        self._process.start()

    def join(self, timeout=None):
        """等待子进程结束"""
        self._process.join(timeout)

    def is_alive(self) -> bool:
        """检查子进程是否仍在运行"""
        return self._process.is_alive()

    def terminate(self):
        """强制终止子进程（超时保护用）"""
        # 必须先 cancel_join_thread，防止子进程写满 Queue pipe 导致卡死
        self._result_queue.cancel_join_thread()
        self._process.terminate()

    def get_result(self, timeout: float = 60) -> Any:
        """
        阻塞等待子进程结果。

        Args:
            timeout: 最大等待秒数，超时抛出 TimeoutError

        Returns:
            任务函数的返回值

        Raises:
            RuntimeError: 子进程内部抛出异常时
            TimeoutError: 等待超时时
        """
        try:
            res = self._result_queue.get(timeout=timeout)
            if res["status"] == "error":
                raise RuntimeError(
                    f"Worker [{self.name}] failed: {res['error']}\n{res['traceback']}"
                )
            return res["result"]
        except queue.Empty:
            raise TimeoutError(f"Worker [{self.name}] timed out after {timeout}s")

    def checkpoint(self) -> Optional["TaskBrief"]:
        """
        尝试读取子进程写入的 checkpoint。
        在 terminate() 之前调用，抢救中间状态。

        Returns:
            TaskBrief 对象，如果子进程没有写 checkpoint 则返回 None
        """
        return self._checkpoint_reader.read()
