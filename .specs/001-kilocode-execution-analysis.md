# KiloCode + GLM 执行阻塞问题分析

> updated_by: KiloCode - GLM-5
> updated_at: 2026-03-04 16:05:00

## 问题描述

使用 KiloCode + GLM 执行一段 prompt 时，程序停下来等待用户输入，console 停在该位置，既没有继续执行，也没有报错。

## 技术术语

这种现象在技术上有几个常见的术语：

1. **阻塞 (Blocking)** - 最常用的技术术语。程序在等待 I/O 操作（如用户输入）时被阻塞，无法继续执行后续代码。

2. **等待输入 (Waiting for Input)** - 描述性术语，指程序处于等待状态，期待用户通过标准输入 (stdin) 提供数据。

3. **同步阻塞 (Synchronous Blocking)** - 强调这是同步操作，程序会一直停在那里直到输入完成。

4. **交互式进程挂起 (Interactive Process Hang)** - 程序在某个内部路径等待用户交互，但外部调用者无法感知或提供输入。

5. **隐式输入等待 (Implicit Input Wait)** - 程序内部存在等待用户确认的逻辑，但未明确通知调用者。

## 代码分析

### 文件位置

[`packages/coders/kilocode.py`](../packages/coders/kilocode.py)

### stdin 处理

代码第 89 行已设置 `stdin=subprocess.DEVNULL`：

```python
process = subprocess.Popen(
    full_command,
    stdin=subprocess.DEVNULL,  # 已处理 stdin
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    ...
)
```

理论上，这应该避免等待用户输入。但问题仍然可能发生。

### 可能的根本原因

**最可能的原因：`kilocode` 命令本身是交互式的**

代码通过 `powershell -Command` 执行 `kilocode` 命令。如果 `kilocode` CLI 内部有交互式确认（如 "是否继续？[Y/n]"），即使父进程的 stdin 是 DEVNULL，子进程可能会：

1. 打开新的 TTY/控制台
2. 或者因为没有收到输入而无限等待
3. 或者在某些内部路径卡住

### 心跳日志机制

代码第 127-140 行实现了心跳日志：

```python
next_heartbeat = start_time + 5

while True:
    return_code = process.poll()
    now = time.monotonic()

    if return_code is not None:
        logger.info(f"进程已结束，返回码: {return_code}")
        break

    if now >= next_heartbeat:
        elapsed_seconds = int(now - start_time)
        logger.info(f"命令仍在执行中，已等待 {elapsed_seconds}s，PID: {process.pid}")
        next_heartbeat = now + 5

    time.sleep(0.2)
```

**判断方法**：
- 如果心跳日志还在输出 → 说明进程仍在运行，可能在等待 kilocode 内部的某些操作
- 如果心跳日志停止 → 说明进程已结束，但可能卡在某个线程同步上

### Windows PowerShell 特殊性

在 Windows 上使用 `powershell -Command` 执行命令时，PowerShell 可能会：

1. 启动交互式控制台窗口
2. 等待用户输入确认（如 UAC 提示、权限确认等）
3. 在某些安全策略下暂停执行

## 排查建议

### 1. 检查日志输出

观察心跳日志是否继续输出：
- **继续输出** → 进程仍在运行，问题在 `kilocode` 内部
- **停止输出** → 进程已结束，问题在 Python 线程同步

### 2. 检查 `kilocode` 命令的非交互模式

如果 `kilocode` 支持非交互模式，添加相关标志：
- `--yes` / `-y`：自动确认
- `--non-interactive`：非交互模式
- `--no-input`：禁用输入

### 3. 检查子进程状态

在任务管理器或 Process Explorer 中查看：
- `kilocode` 进程是否存在
- CPU 使用率是否为 0（等待状态）
- 是否有子进程被创建

### 4. 测试命令行直接执行

在 PowerShell 中直接执行相同命令，观察是否需要交互：

```powershell
powershell -Command "kilocode <你的命令>"
```

## 建议修复方案

### 方案 1：添加非交互标志

如果 `kilocode` 支持，在命令中添加非交互标志：

```python
# 修改命令构造逻辑
if is_windows():
    command = f"kilocode --non-interactive {original_command}"
```

### 方案 2：设置环境变量

某些 CLI 工具支持通过环境变量禁用交互：

```python
env = os.environ.copy()
env["CI"] = "true"  # 许多工具在 CI 环境下自动禁用交互
env["DEBIAN_FRONTEND"] = "noninteractive"
# 或特定于工具的环境变量
```

### 方案 3：使用 PTY 替代

如果 `kilocode` 必须要 TTY，可以考虑使用伪终端：

```python
# 仅适用于 Unix 系统
import pty
master, slave = pty.openpty()
process = subprocess.Popen(
    full_command,
    stdin=slave,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    ...
)
```

### 方案 4：超时机制

添加命令执行超时：

```python
try:
    process.wait(timeout=300)  # 5 分钟超时
except subprocess.TimeoutExpired:
    process.kill()
    logger.error("命令执行超时，已终止")
```

## 结论

该问题最可能是由于 `kilocode` CLI 工具内部的交互式确认导致的阻塞。需要进一步确认 `kilocode` 是否支持非交互模式，并在代码中添加相应的处理。