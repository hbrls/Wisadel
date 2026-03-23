"""KiloCode 命令执行模块 - 跨平台命令执行核心逻辑

此模块提供跨平台的命令执行功能，支持 Windows PowerShell 和 macOS/Linux bash。

日志配置说明：
- 模块直接使用 loguru 的 logger
- 独立日志文件由应用层（dashboard/logger_config.py）配置
- 通过 filter=lambda record: record["name"] == "coders.kilocode" 实现日志分离
"""

import os
import re
import subprocess
import sys
import threading
import time
from uuid import uuid4

from loguru import logger

from coders.platform_utils import is_linux, is_macos, is_windows


class KiloCode:
    """跨平台命令执行器"""

    def _validate_cwd(self, cwd: str | None) -> str:
        if cwd is None:
            cwd = os.path.expanduser("~")

        logger.debug(f"验证工作目录: {cwd}")

        if not os.path.exists(cwd):
            raise FileNotFoundError(f"工作目录不存在: {cwd}")

        if not os.access(cwd, os.R_OK | os.W_OK):
            raise PermissionError(f"工作目录权限不足: {cwd}")

        return cwd

    def probe(self, cwd: str | None = None) -> None:
        """探测 kilocode 命令是否可用

        Args:
            cwd: 工作目录路径，默认为用户主目录

        Note:
            - Windows: 使用 powershell -Command kilocode --version
            - macOS/Linux: 使用 bash -c kilocode --version
            - 成功时输出版本信息，失败时输出错误日志
        """
        cwd = self._validate_cwd(cwd)

        if is_windows():
            cmd = ["powershell", "-Command", "kilocode --version"]
            kwargs = {"encoding": "utf-8", "errors": "replace"}
        elif is_macos() or is_linux():
            cmd = ["bash", "-c", "kilocode --version"]
            kwargs = {}
        else:
            logger.error(f"不支持的平台: {sys.platform}")
            return

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                **kwargs,
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"kilocode 探针成功: {result.stdout.strip()}")
            else:
                logger.error("kilocode 探针失败: 未找到 kilocode 命令或执行出错")
        except Exception as e:
            logger.error(f"kilocode 探针异常: {type(e).__name__}: {e}")

    def _execute(
        self, args: list[str], cwd: str
    ) -> subprocess.CompletedProcess | None:
        """执行子进程（内部方法）

        Args:
            args: 完整的命令参数列表
            cwd: 工作目录路径

        Returns:
            成功时返回 subprocess.CompletedProcess 对象，失败时返回 None
        """
        logger.info(f"执行命令: {args}")

        try:
            start_time = time.monotonic()
            process = subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=cwd,
            )
            logger.debug(f"子进程已启动，PID: {process.pid}")

            stdout_lines: list[str] = []
            stderr_lines: list[str] = []

            def stream_reader(stream, line_logger, tag: str, line_buffer: list[str]):
                try:
                    for line in iter(stream.readline, ""):
                        stripped_line = line.rstrip("\r\n")
                        if stripped_line:
                            line_logger(f"{tag}: {stripped_line}")
                        line_buffer.append(line)
                finally:
                    stream.close()

            stdout_thread = threading.Thread(
                target=stream_reader,
                args=(process.stdout, logger.debug, "[Coder Coooding]", stdout_lines),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=stream_reader,
                args=(process.stderr, logger.debug, "[Coder Thinking]", stderr_lines),
                daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()
            logger.debug("输出读取线程已启动")

            next_heartbeat = start_time + 5

            while True:
                return_code = process.poll()
                now = time.monotonic()

                if return_code is not None:
                    logger.debug(f"进程已结束，返回码: {return_code}")
                    break

                if now >= next_heartbeat:
                    elapsed_seconds = int(now - start_time)
                    logger.debug(
                        f"命令仍在执行中，已等待 {elapsed_seconds}s，PID: {process.pid}"
                    )
                    next_heartbeat = now + 10

                time.sleep(0.2)

            logger.debug("开始等待输出线程结束...")
            stdout_thread.join(timeout=1)
            logger.debug(f"stdout 线程状态: alive={stdout_thread.is_alive()}")
            stderr_thread.join(timeout=1)
            logger.debug(f"stderr 线程状态: alive={stderr_thread.is_alive()}")

            stdout_text = "".join(stdout_lines)
            stderr_text = "".join(stderr_lines)
            logger.debug(
                f"输出收集完成: stdout={len(stdout_text)} 字符, stderr={len(stderr_text)} 字符"
            )
            completed_process = subprocess.CompletedProcess(
                args=args,
                returncode=return_code,
                stdout=stdout_text,
                stderr=stderr_text,
            )

            if return_code == 0:
                elapsed_seconds = int(time.monotonic() - start_time)
                logger.debug(
                    f"命令执行成功，返回码: {return_code}，耗时: {elapsed_seconds}s"
                )
                return completed_process

            elapsed_seconds = int(time.monotonic() - start_time)
            logger.error(
                f"命令执行失败，返回码: {return_code}，耗时: {elapsed_seconds}s"
            )
            return None
        except Exception as e:
            logger.error(f"命令执行异常: {type(e).__name__}: {e}")
            return None

    def run_command(
        self, command: str, cwd: str | None = None
    ) -> subprocess.CompletedProcess | None:
        """执行跨平台 shell 命令

        Args:
            command: 要执行的命令字符串
            cwd: 工作目录路径，默认为用户主目录

        Returns:
            成功时返回 subprocess.CompletedProcess 对象，失败时返回 None

        Note:
            - Windows: 使用 powershell -Command 执行
            - macOS/Linux: 使用 bash -c 执行
            - 子进程 stdin 使用 DEVNULL，避免标准输入等待
            - 流式输出 stdout/stderr 到日志
            - 每 5 秒输出心跳日志
        """
        cwd = self._validate_cwd(cwd)

        if is_windows():
            full_command = ["powershell", "-Command", command.strip()]
        elif is_macos() or is_linux():
            full_command = ["bash", "-c", command.strip()]
        else:
            logger.error(f"不支持的平台: {sys.platform}")
            return None

        return self._execute(full_command, cwd)

    def run_prompt(
        self, prompt: str, cwd: str | None = None
    ) -> subprocess.CompletedProcess | None:
        """执行 kilocode 提示词

        Args:
            prompt: 提示词字符串
            cwd: 工作目录路径，默认为用户主目录

        Returns:
            成功时返回 subprocess.CompletedProcess 对象，失败时返回 None

        Note:
            - Windows: 通过 PowerShell 变量传递 prompt，避免特殊字符被解释
            - macOS/Linux: 通过 bash 单引号传递 prompt
        """
        cwd = self._validate_cwd(cwd)

        if is_windows():
            # PowerShell 单引号字符串是字面量，不解释任何特殊字符
            # 唯一需要转义的是单引号本身（' → ''）
            escaped = prompt.strip().replace("'", "''")
            ps_script = f"$p = '{escaped}'; kilocode run --model dashscope/glm-5 $p"
            full_command = ["powershell", "-Command", ps_script]
        elif is_macos() or is_linux():
            # bash 单引号字符串是字面量，转义单引号：' → '\''
            escaped = prompt.strip().replace("'", "'\\''")
            bash_script = f"kilocode run --model dashscope/glm-5 '{escaped}'"
            full_command = ["bash", "-c", bash_script]
        else:
            logger.error(f"不支持的平台: {sys.platform}")
            return None

        return self._execute(full_command, cwd)


_default_instance = KiloCode()


def probe(cwd: str | None = None) -> None:
    """探测 kilocode 命令是否可用（模块级便捷函数）

    Args:
        cwd: 工作目录路径，默认为用户主目录
    """
    _default_instance.probe(cwd)


def create_session() -> str | None:
    """创建 kilocode 会话并返回会话 ID
    
    执行 kilocode 命令创建新会话，并从输出中提取会话 ID。
    
    Returns:
        成功时返回会话 ID 字符串，失败时返回 None
    """
    session_id = uuid4()
    command = f'''kilocode run --model dashscope/glm-5 "Remember this KiloCodeSessionId={session_id}. Exit immediately." --print-logs'''
    
    result = _default_instance.run_command(command)
    
    if result is None:
        logger.error("创建会话失败: 命令执行失败")
        return None
    
    # 获取 stdout 和 stderr 的最后 20 行
    stdout_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
    stderr_lines = result.stderr.strip().split('\n') if result.stderr.strip() else []
    
    # 合并 stdout 和 stderr，取最后 20 行
    all_lines = stdout_lines + stderr_lines
    last_20_lines = all_lines[-20:] if len(all_lines) > 20 else all_lines
    output_text = '\n'.join(last_20_lines)
    
    # 使用正则表达式从输出中解析 session ID
    # 输出格式: "stderr: INFO  2026-03-23T10:42:09 +1ms service=session.prompt sessionID=<id> exiting loop"
    # 匹配 "service=session.prompt sessionID=<id> exiting loop"
    # session ID 包含大小写字母、数字、中划线、下划线
    pattern_exiting = r'service=session\.prompt\s+sessionID=([a-zA-Z0-9\-_]+)\s+exiting\s+loop'
    # 匹配 "service=session.prompt sessionID=<id> cancel"
    pattern_cancel = r'service=session\.prompt\s+sessionID=([a-zA-Z0-9\-_]+)\s+cancel'

    match_exiting = re.search(pattern_exiting, output_text)
    match_cancel = re.search(pattern_cancel, output_text)
    
    id0 = match_exiting.group(1) if match_exiting else None
    id1 = match_cancel.group(1) if match_cancel else None

    # 验证两个 ID 是否相同
    if id0 and id1 and id0 == id1:
        logger.info(f"创建会话成功，会话 ID: {id0}")
        return id0
    else:
        logger.error(f"会话 ID 验证失败: exiting_id={id0}, cancel_id={id1}")
        return None


def run_command(command: str, cwd: str | None = None) -> subprocess.CompletedProcess | None:
    """执行跨平台命令（模块级便捷函数）

    Args:
        command: 要执行的命令字符串
        cwd: 工作目录路径，默认为用户主目录

    Returns:
        成功时返回 subprocess.CompletedProcess 对象，失败时返回 None
    """
    return _default_instance.run_command(command, cwd)


def run_prompt(prompt: str, cwd: str | None = None) -> subprocess.CompletedProcess | None:
    """执行 kilocode 提示词（模块级便捷函数）

    Args:
        prompt: 提示词字符串
        cwd: 工作目录路径，默认为用户主目录

    Returns:
        成功时返回 subprocess.CompletedProcess 对象，失败时返回 None
    """
    return _default_instance.run_prompt(prompt, cwd)
