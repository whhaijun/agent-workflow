"""
轻量 RPC Server - 基于 Python 标准库 xmlrpc
让主进程暴露工具（如 memory_read/write）给子进程调用。

用法（主进程）：
    server = AgentRPCServer(port=8765)
    server.register("memory_read", my_memory_read_fn)
    server.start()  # 后台线程运行，不阻塞主进程

用法（子进程 / Worker）：
    client = AgentRPCClient(port=8765)
    result = client.call("memory_read", key="hot.md")
"""
import threading
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy, Fault


class AgentRPCServer:
    """
    在后台线程中运行的轻量 XML-RPC Server。
    主进程通过 register() 暴露工具函数，子进程通过 AgentRPCClient 调用。
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """
        Args:
            host: 监听地址，默认仅本机访问（127.0.0.1）
            port: 监听端口，默认 8765
        """
        self.host = host
        self.port = port
        self._server = SimpleXMLRPCServer(
            (host, port),
            logRequests=False,   # 关闭请求日志，减少噪声
            allow_none=True      # 允许传输 None 值
        )
        self._thread: threading.Thread | None = None

    def register(self, name: str, fn):
        """
        注册一个可被子进程调用的工具函数。

        Args:
            name: 函数在 RPC 中的名称（客户端用此名称调用）
            fn:   可调用对象，参数必须是 XML-RPC 可序列化类型
        """
        self._server.register_function(fn, name)

    def start(self):
        """
        在后台守护线程中启动 RPC Server，不阻塞主进程。
        主进程退出时后台线程自动终止（daemon=True）。
        """
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="agent-rpc-server"
        )
        self._thread.start()

    def stop(self):
        """优雅停止 RPC Server"""
        self._server.shutdown()


class AgentRPCClient:
    """
    XML-RPC 客户端，供子进程调用主进程注册的工具函数。
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """
        Args:
            host: RPC Server 地址
            port: RPC Server 端口
        """
        self._proxy = ServerProxy(
            f"http://{host}:{port}/",
            allow_none=True   # 允许接收 None 返回值
        )

    def call(self, method: str, **kwargs):
        """
        调用主进程注册的工具函数。

        Args:
            method: 工具函数名称（与 server.register 的 name 一致）
            **kwargs: 传递给工具函数的关键字参数

        Returns:
            工具函数的返回值

        Raises:
            ConnectionRefusedError: RPC Server 未启动或不可达
            RuntimeError: RPC Server 端执行出错（Fault）
        """
        try:
            fn = getattr(self._proxy, method)
            return fn(**kwargs)
        except Fault as e:
            raise RuntimeError(f"RPC call [{method}] failed on server: {e.faultString}")
        except ConnectionRefusedError:
            raise ConnectionRefusedError(
                f"Cannot connect to RPC Server at {self._proxy._ServerProxy__host}. "
                "Ensure AgentRPCServer.start() was called before spawning workers."
            )
