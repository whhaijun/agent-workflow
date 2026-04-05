# integrations/parallel — 原生并行执行模块

零外部依赖，全部使用 Python 标准库，兼容 Claude Code / Codex / 独立部署等无 OpenClaw 环境。

---

## 什么场景用并行

满足以下任意条件时，应考虑并行执行：

- **≥ 2 个独立子任务**：任务之间无数据依赖，可以同时进行
- **预计总耗时 > 30s**：串行执行明显浪费时间
- **典型场景**：同时读取多个文件、并发调用多个外部 API、多 Agent 分工处理不同模块

> 每批并行上限为 `max_workers=3`，与团队 WBS 规范保持一致。

---

## AgentPool 快速示例

### 示例 1：并行执行多个独立分析任务

```python
from integrations.parallel.pool import AgentPool

def analyze_module(module_name: str) -> dict:
    # 模拟分析逻辑（实际可调用 LLM、读取文件等）
    return {"module": module_name, "issues": []}

pool = AgentPool(max_workers=3)
pool.submit("auth",    analyze_module, args=("auth",))
pool.submit("payment", analyze_module, args=("payment",))
pool.submit("profile", analyze_module, args=("profile",))

results = pool.run_all(timeout=120)

for name, res in results.items():
    if res["status"] == "ok":
        print(f"{name}: {res['result']}")
    else:
        print(f"{name} 失败: {res['error']}")
```

### 示例 2：超时保护 + 错误隔离

```python
from integrations.parallel.pool import AgentPool

def slow_task(n: int) -> str:
    import time
    time.sleep(n)
    return f"done after {n}s"

def bad_task() -> str:
    raise ValueError("something went wrong")

pool = AgentPool(max_workers=3)
pool.submit("fast",  slow_task, args=(1,))
pool.submit("slow",  slow_task, args=(200,))  # 会超时
pool.submit("error", bad_task)               # 会失败

results = pool.run_all(timeout=10)
# results["fast"]  -> {"status": "ok",      "result": "done after 1s"}
# results["slow"]  -> {"status": "timeout", "error": "Worker [slow] timed out after 10s"}
# results["error"] -> {"status": "error",   "error": "Worker [error] failed: ..."}
```

### 示例 3：超过 max_workers 时自动分批

```python
from integrations.parallel.pool import AgentPool

def fetch_data(key: str) -> dict:
    return {"key": key, "data": "..."}

pool = AgentPool(max_workers=3)  # 每批最多 3 个

# 提交 6 个任务，自动分 2 批执行
for i in range(6):
    pool.submit(f"task_{i}", fetch_data, args=(f"key_{i}",))

results = pool.run_all(timeout=60)
# 第 1 批：task_0, task_1, task_2 并行
# 第 2 批：task_3, task_4, task_5 并行（第 1 批全部完成后启动）
```

---

## AgentRPCServer 使用场景

当子进程需要访问主进程的共享资源时（如内存文件、配置、缓存），使用 RPC 桥接。

**典型场景**：子进程 Worker 需要读写 `memory/hot.md`，但文件 I/O 应由主进程统一管理，避免并发写冲突。

```python
from integrations.parallel.rpc_server import AgentRPCServer, AgentRPCClient
from integrations.parallel.pool import AgentPool

# === 主进程 ===
def memory_read(key: str) -> str:
    with open(f"memory/{key}") as f:
        return f.read()

server = AgentRPCServer(port=8765)
server.register("memory_read", memory_read)
server.start()  # 后台线程，不阻塞

# 子任务函数（在子进程中运行）
def worker_task(key: str) -> str:
    client = AgentRPCClient(port=8765)
    content = client.call("memory_read", key=key)
    return f"got {len(content)} chars from {key}"

pool = AgentPool()
pool.submit("reader_1", worker_task, args=("hot.md",))
pool.submit("reader_2", worker_task, args=("archive.md",))
results = pool.run_all(timeout=30)

server.stop()
```

---

## 与 OpenClaw sessions_spawn 的关系

| 环境 | 推荐方案 |
|------|---------|
| 有 OpenClaw | 优先使用 `sessions_spawn`，原生多 Agent 隔离更完整 |
| 无 OpenClaw（Claude Code / Codex / 独立部署） | 使用本模块 `AgentPool`，零依赖，行为一致 |

两者接口不同，但语义相同：提交独立子任务 → 并行执行 → 收集结果。

迁移时只需替换任务提交方式，业务逻辑（task_fn）无需修改。

---

## 注意事项

1. **每批 ≤ 3 个**：`max_workers` 默认为 3，与团队 WBS 规范一致，避免资源竞争
2. **task_fn 必须可序列化**：子进程通过 `multiprocessing` 传递，lambda 和闭包可能无法序列化，推荐使用模块级函数
3. **避免共享可变状态**：子进程有独立内存空间，主进程的变量修改不会传播到子进程
4. **RPC 参数类型限制**：`xmlrpc` 仅支持基础类型（str / int / float / list / dict / bool / None），复杂对象需先序列化
5. **macOS 多进程注意**：在 `if __name__ == "__main__":` 保护块中调用 `pool.run_all()`，避免子进程递归 fork
