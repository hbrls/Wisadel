"""
日志模块（全局配置）

使用 Loguru 配置开发环境控制台日志和打包后的文件日志。
"""

import sys
from pathlib import Path

from loguru import logger

from coders.platform_utils import get_log_dir


def _is_executable() -> bool:
    """判断是否在打包后的可执行文件中运行。"""
    return hasattr(sys, "frozen")


def init_logger():
    """初始化全局日志配置。"""
    logger.remove()

    if _is_executable():
        log_dir = Path(get_log_dir("w-execute"))
        app_log_file = log_dir / "w-execute-{time:YYYY-MM-DD}.log"
        kilocode_log_file = log_dir / "w-execute-KiloCode-{time:YYYY-MM-DD}.log"

        logger.add(
            app_log_file,
            rotation="1 MB",
            retention="10 days",
            level="DEBUG",
            encoding="utf-8",
            filter=lambda record: record["name"] != "coders.kilocode",
        )
        logger.add(
            kilocode_log_file,
            filter=lambda record: record["name"] == "coders.kilocode",
            rotation="1 MB",
            retention="10 days",
            level="DEBUG",
            encoding="utf-8",
        )
    else:
        logger.add(sys.stderr, level="DEBUG")


init_logger()
