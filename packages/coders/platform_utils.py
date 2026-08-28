"""平台工具函数 - 跨平台系统判断"""

import os
import sys


def is_windows() -> bool:
    """判断当前系统是否为 Windows"""
    return sys.platform == "win32"


def is_macos() -> bool:
    """判断当前系统是否为 macOS"""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """判断当前系统是否为 Linux"""
    return sys.platform.startswith("linux")


def get_subprocess_env() -> dict[str, str]:
    """获取用于启动外部命令的环境变量。"""
    env = os.environ.copy()

    if is_macos():
        home_dir = env.get("HOME") or os.path.expanduser("~")
        path_items = [
            os.path.join(home_dir, "backstage"),
            "/opt/homebrew/bin",
            "/opt/homebrew/sbin",
            "/opt/homebrew/opt/node@22/bin",
            *env.get("PATH", "").split(os.pathsep),
        ]
        env["PATH"] = os.pathsep.join(
            dict.fromkeys(item for item in path_items if item)
        )

    return env


def get_log_dir(app_name: str = "Dashboard") -> str:
    """获取日志目录（跨平台）

    Args:
        app_name: 应用名称，默认为 "Dashboard"

    Returns:
        str: 日志目录路径
    """
    if is_windows():
        log_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "Temp",
            app_name,
        )
    elif is_macos():
        log_dir = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Logs",
            app_name,
        )
    else:
        log_dir = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            app_name,
            "logs",
        )

    os.makedirs(log_dir, exist_ok=True)
    return log_dir
