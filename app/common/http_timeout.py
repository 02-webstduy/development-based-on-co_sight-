# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

import os
import threading
from typing import Any, Callable, Tuple, TypeVar

T = TypeVar("T")


def get_tool_exec_timeout() -> float:
    """Max seconds for a single tool invocation (agent thread pool)."""
    try:
        value = float(os.environ.get("TOOL_EXEC_TIMEOUT", "60"))
    except (TypeError, ValueError):
        value = 60.0
    return max(1.0, value)


def get_http_timeout() -> Tuple[float, float]:
    """(connect_timeout, read_timeout) for requests library."""
    try:
        connect = float(os.environ.get("HTTP_TIMEOUT_CONNECT", "5"))
        read = float(os.environ.get("HTTP_TIMEOUT_READ", "30"))
    except (TypeError, ValueError):
        connect, read = 5.0, 30.0
    return max(1.0, connect), max(1.0, read)


def tool_timeout_message(function_name: str, timeout: float) -> str:
    return (
        f"ToolTimeoutError: `{function_name}` exceeded {timeout}s execution limit. "
        "Try a different tool, simplify the query, or mark_step as blocked."
    )


def run_with_timeout(func: Callable[..., T], timeout: float, *args: Any, **kwargs: Any) -> T:
    """Run func in a daemon thread; raise TimeoutError if it does not finish in time."""
    result_container: list[Any] = []
    error_container: list[BaseException] = []

    def target() -> None:
        try:
            result_container.append(func(*args, **kwargs))
        except BaseException as exc:  # noqa: BLE001 — propagate any tool failure
            error_container.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(tool_timeout_message(getattr(func, "__name__", "tool"), timeout))
    if error_container:
        raise error_container[0]
    return result_container[0]
