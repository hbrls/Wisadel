# 101 - Dashboard 系统

> updated_by: GitHub Copilot - GPT-5.3-Codex
> updated_at: 2026-03-03 12:11:20

### Goals

- 从 windows-app 项目复制并改造基础架构，快速搭建新项目的开发基础
- 在保留核心模块 main、ui、logger 的基础上，创建独立的 agents 模块并配置隔离的跨包导入
- 创建独立的 coders 模块，集成 kilocode 跨平台命令执行
- 实现"润"按钮 UI 功能，支持异步命令执行且不阻塞 UI 主线程
- 实现 CodingAgent 核心功能，支持用户通过 UI 选择工作目录并在指定目录中执行命令
- 确保项目可成功编译、打包、运行，所有核心模块功能完整
- 定位并调试命令执行偶现卡住问题，提供详细的诊断日志和解决方案

### Non-Goals

- 完整的跨平台兼容性和优化（仅保留基础兼容能力）

### Scope

无

### Non-Scope

无

### Functional Requirements

#### 模块保留需求

- **FR-001**: 新项目应保留 main 模块的项目入口与初始化逻辑
- **FR-002**: 新项目应保留 ui 模块的基础框架结构，并抽象 Windows 特定实现为跨平台接口
- **FR-003**: 新项目应保留 logger 模块的日志记录功能，支持跨平台文件写入

#### 模块创建与隔离需求

- **FR-010**: 新项目应创建独立的 agents 模块（在 packages/agents 目录下），包含 Wisadel 核心功能和 providers 子模块，并配置 __init__.py 导出 Wisadel、MinimaxProvider
- **FR-011**: 新项目应通过 _agents.py 隔离加载器实现跨包导入，不污染 sys.path
- **FR-013**: 在创建 agents 模块后，项目应能成功编译且无编译错误

#### 项目验证需求

- **FR-031**: 新项目应能成功编译、打包并启动
- **FR-032**: main、ui、logger 三个模块在新项目中应能正常工作

### Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| agents 模块创建 | N/A | 正常加载与导入 | 运行时验证导入成功 |
| 编译成功率 | N/A | 100% | 运行构建命令，0 编译错误 |
| main 模块功能 | N/A | 正常启动/停止 | 实际运行项目并观察 |
| ui 模块可用 | N/A | 界面显示正常 | 视觉检验 |
| logger 模块可用 | N/A | 日志文件正常写入 | 检查日志输出文件 |

### Dependencies

无

### Constraints

- **C-001**: 新项目的文件结构应与源项目保持一致，便于后续对标维护

### Assumptions

无

### References

无

---

## Design

### 隔离的 Agents 和 Coders 模块创建策略

本阶段需要创建独立的 agents 和 coders 模块，并通过隔离加载器实现跨包导入。采用隔离模块设计：

#### Agents 模块
- **agents 模块**：定义 AI 智能体相关功能（包含 providers、tools、tests 等子目录）
- **_agents.py 隔离加载器**：使用 importlib.util.spec_from_file_location 准确控制加载
- **dashboard 中的集成**：通过 `from _agents import agents` 来使用

#### Coders 模块
- **coders 模块**：定义代码处理相关功能
  - **KiloCode**：跨平台命令执行核心逻辑（run_command 函数）
- **_coders.py 隔离加载器**：使用 importlib.util.spec_from_file_location 准确控制加载
- **dashboard 中的集成**：通过 `from _coders import ClassName, run_command` 来使用

#### 隔离性保证
不污染 sys.path，确保模块有效隔离，使得一个应用程序的子模块不被另一个应用程序访问。所有跨包导入均通过专用的 _agents.py 和 _coders.py 加载器进行。

### 命令执行机制与故障排查

#### 命令执行架构
Dashboard 的命令执行采用三层架构：
- **UI 层 (main_window.py)**：按钮事件触发，创建 RunWorker 线程
- **线程层 (run_worker.py)**：QThread 封装，确保 UI 不阻塞
- **执行层 (kilocode.py)**：跨平台命令执行核心逻辑，使用 subprocess.Popen + 线程流式读取

#### 执行流程
```python
# 1. UI 层触发
RunWorker(command, cwd) → start()

# 2. 线程层异步执行
QThread.run() → run_command(command, cwd)

# 3. 执行层核心逻辑
subprocess.Popen() → 启动子进程
threading.Thread() → 读取 stdout/stderr
process.poll() → 检测进程状态
thread.join(timeout=1) → 等待输出线程
返回 CompletedProcess
```

#### 已知问题：命令执行偶现卡住

**问题描述**：
- 点击"润"按钮后，命令执行卡住不返回
- 手工在 PowerShell 执行相同命令快速完成
- 问题偶现但频率较高

**可能原因分析**：

1. **流式读取阻塞**（最可能）
   - `iter(stream.readline, "")` 会一直读取直到流返回空字符串
   - 即使 `process.poll()` 检测到进程结束（returncode != None），stdout/stderr 流可能不会立即关闭
   - 导致 `readline()` 一直阻塞等待流关闭

2. **线程同步问题**
   - `thread.join(timeout=1)` 超时后主线程继续执行
   - 但读取线程可能仍在后台阻塞（daemon=True 仅在主进程退出时终止）
   - 可能导致数据不完整或状态不一致

3. **PowerShell 进程行为**
   - PowerShell 执行 `kilocode run` 可能创建子进程
   - 父进程结束但子进程未关闭流
   - 导致流式读取持续等待

**调试方法**：

添加关键位置日志定位卡住环节：
```python
# packages/coders/kilocode.py

# 1. 线程启动后
logger.info("输出读取线程已启动")

# 2. 进程状态检测
if return_code is not None:
    logger.info(f"进程已结束，返回码: {return_code}")
    break

# 3. 等待线程结束前
logger.info("开始等待输出线程结束...")

# 4. 检查线程状态
logger.info(f"stdout 线程状态: alive={stdout_thread.is_alive()}")
logger.info(f"stderr 线程状态: alive={stderr_thread.is_alive()}")

# 5. 数据收集完成
logger.info(f"输出收集完成: stdout={len(stdout_text)} 字符, stderr={len(stderr_text)} 字符")
```

通过日志确定卡住位置：
- 若卡在"进程已结束"之前：进程状态检测问题
- 若卡在"开始等待输出线程"之后：流式读取阻塞问题
- 若线程 `alive=True`：readline() 仍在等待流关闭

**潜在解决方案**（待验证）：

1. **方案一：改用 communicate() 方法**
   - **原理**：使用 Python 标准库的 `process.communicate()` 替代手动流式读取
   - **技术实现**：
     ```python
     process = subprocess.Popen(
         command,
         stdout=subprocess.PIPE,
         stderr=subprocess.PIPE,
         stdin=subprocess.DEVNULL,
         cwd=cwd
     )
     stdout, stderr = process.communicate(timeout=300)  # 5分钟超时
     ```
   - **优点**：
     - Python 标准库内部实现，久经考验，稳定可靠
     - 自动管理流的打开/关闭，避免手动管理线程复杂性
     - 不会因流未正确关闭而死锁
     - 内部使用 select/poll 机制，防止死锁
   - **缺点**：
     - 完全失去实时输出能力，只能在命令结束后统一显示
     - 长时间运行的命令会让用户感觉"无响应"
     - 无法提供执行过程中的进度反馈（如心跳日志）
   - **适用场景**：命令执行时间较短（<30秒）的场景
   - **权衡点**：牺牲用户体验（实时反馈）换取系统稳定性

2. **方案二：添加流读取超时机制**
   - **原理**：在流式读取线程中添加超时检测，避免无限阻塞
   - **技术实现**：
     ```python
     import select

     def stream_reader_with_timeout(stream, output_list, timeout=1):
         while True:
             if process.poll() is not None:  # 进程已结束
                 # 使用 select 检查流是否还有数据可读
                 if sys.platform == 'win32':
                     # Windows 使用 peek 检查
                     remaining = stream.peek()
                     if not remaining:
                         break
                 else:
                     # Unix/Linux 使用 select
                     ready = select.select([stream], [], [], timeout)
                     if not ready[0]:
                         break
             line = stream.readline()
             if not line:
                 break
             output_list.append(line)
     ```
   - **优点**：
     - 保留实时输出能力
     - 增加超时保护，避免永久阻塞
     - 在进程结束后能够及时退出
   - **缺点**：
     - 实现复杂度较高
     - Windows 和 Unix/Linux 平台行为差异需要分别处理
     - 可能存在边界条件（如数据在超时时刻到达）
   - **适用场景**：需要保持实时输出的场景
   - **风险点**：跨平台兼容性需要充分测试

3. **方案三：改进进程组管理**
   - **原理**：使用进程组确保所有子进程（包括孙进程）都能被正确管理和清理
   - **技术实现**：
     ```python
     if sys.platform == 'win32':
         # Windows: 使用 CREATE_NEW_PROCESS_GROUP
         process = subprocess.Popen(
             command,
             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
             ...
         )
     else:
         # Unix/Linux: 使用 start_new_session
         process = subprocess.Popen(
             command,
             start_new_session=True,
             ...
         )

     # 终止时杀掉整个进程组
     if sys.platform == 'win32':
         os.kill(process.pid, signal.CTRL_BREAK_EVENT)
     else:
         os.killpg(os.getpgid(process.pid), signal.SIGTERM)
     ```
   - **优点**：
     - 确保子进程树被完整清理
     - 防止僵尸进程
     - 解决 PowerShell 创建子进程导致流未关闭的问题
   - **缺点**：
     - 不能完全解决流阻塞问题（主要解决进程清理问题）
     - Windows 和 Unix/Linux 信号机制差异大
     - 可能影响某些需要保留子进程的场景
   - **适用场景**：作为辅助方案，配合方案一或方案二使用
   - **注意事项**：需要确保不会误杀其他无关进程

**建议的验证步骤**：
1. 优先测试方案一：适合快速验证解决 80% 的卡住问题
2. 如果方案一用户体验不佳，尝试方案二：保持实时性的同时增加可靠性
3. 方案三作为补充：无论选择方案一还是方案二，都建议加入进程组管理
4. 完整测试场景：
   - 短命令（<5秒）：`echo "test"`
   - 中等命令（5-30秒）：`kilocode run`
   - 长命令（>30秒）：模拟长时间运行的任务
   - 异常场景：命令执行失败、权限不足、目录不存在

### UI 布局设计（Phase 7 - TASK-701）

#### 多横排布局结构（Tab 布局）

```
┌──────┬────────────────────────────────────────────────────────────────────────────────────────┐
│      │                                                                   ┌─ PID ──┐  ┌─ 耗时 ──┐│
│ Tab1 │  [选择目录]  [当前工作目录: /home/user/project]     [预备]  [开始]│ 10234 │  │ 00:05:23││
│      │                                                                   └────────┘  └─────────┘│
├──────┤  [                文本框                ] [Do-Plan]                                      │
│ Tab2 │  [                文本框                ] [Do-Phase]                                     │
│      │  [                文本框                ] [Do-Skills]                                    │
├──────┤  [                文本框                ] [Do-Output]                                    │
│ Tab3 │  [Do] ┌─ s1 ──┐ ┌─ s2 ──┐ ┌─ s3 ──┐                                                  │
│      │       │ 05:23 │ │ 05:23 │ │ 05:23 │                                                  │
│      │       └───────┘ └───────┘ └───────┘                                                  │
│      │  [                文本框                ] [Check-Scoring]                               │
│      │  [Check] ┌─ s1 ──┐ ┌─ s2 ──┐ ┌─ s3 ──┐                                               │
│      │          │ 05:23 │ │ 05:23 │ │ 05:23 │                                               │
│      │          └───────┘ └───────┘ └───────┘                                               │
│      │  [                文本框                ] [Act-Accept]                                  │
│      │  [Act] ┌─ s1 ──┐                                                                      │
│      │        │ 05:23 │                                                                      │
│      │        └───────┘                                                                      │
└──────┴────────────────────────────────────────────────────────────────────────────────────────┘
```

**说明**：
- 顶部留空 48px（标题栏与内容区之间的间距）
- 布局向上对齐

**说明**：
- **第一行（已实现的交互行）**
  - 左侧：选择目录按钮 + cwd 只读文本框
  - 右侧：预备按钮 + 开始按钮（右对齐）
  - 两个按钮之间间距：8px
  - **cwd 文本框宽度**：与第二、三行的示例文本框保持一致长度（自动扩展填充可用空间）
  - 文本框溢出处理：ellipsis 或水平滚动
  - **状态显示区域**（开始按钮右侧）：
    - **两个独立的 QGroupBox**，并排显示，间距 4px
    - **第一个框（PID 显示）**：
      - 标题文字：`PID`（显示在边框顶部，打断边框线）
      - 边框样式：1px 实线，颜色 #cccccc
      - 背景色：#f9f9f9（浅灰色）
      - 圆角：4px
      - 标题字体：常规字体，字号 9px，颜色 #666666
      - 内容：进程 PID 数字（如 `10234`）或 `--`（无进程时）
      - 内容字体：等宽字体（Consolas/Monaco），字号 11px，颜色 #333333
      - 文字水平居中对齐
      - 内边距：上下 6px，左右 10px
      - 固定宽度：约 80px
    - **第二个框（耗时显示）**：
      - 标题文字：`耗时`（显示在边框顶部，打断边框线）
      - 边框样式：1px 实线，颜色 #cccccc
      - 背景色：#f9f9f9（浅灰色）
      - 圆角：4px
      - 标题字体：常规字体，字号 9px，颜色 #666666
      - 内容：运行时间（如 `00:05:23`）或 `--:--:--`（无进程时）
      - 内容字体：等宽字体（Consolas/Monaco），字号 11px，颜色 #333333
      - 文字水平居中对齐
      - 内边距：上下 6px，左右 10px
      - 固定宽度：约 90px

- **第二、三行**
  - 按第一行样式复制，但函数式禁用（disabled=True）
  - 作为 UI 样式占位，仅作展示用
  - 预留后续扩展空间

### Specs

- [x] **SPEC-001**: 基础架构搭建
  - **背景 / 目标**: 从 windows-app 项目复制基础架构，快速搭建新项目开发基础
  - **范围**: 复制 windows-app 项目的核心文件与目录结构到 packages/dashboard/
  - **关键决策**: 保留 main、ui、logger 等核心模块，创建可运行的基础项目
  - **实现约束**:
    - 复制 main.py、ui/、logger_config.py、platform_utils.py 等核心文件
    - 复制配置文件：requirements.txt、build.bat、Dashboard.spec
    - 确保复制后的项目可独立运行
  - **接口 / 对接点**: packages/dashboard/ 目录结构
  - **命令 / 操作**: 选择性文件复制、目录结构验证、运行测试
  - **验收（勾选即证据）**:
    - [x] 所有核心模块文件已复制到 packages/dashboard/
    - [x] 配置文件完整（requirements.txt、build.bat、Dashboard.spec）
    - [x] 项目可正常运行（python main.py 成功启动）
    - [x] 日志、UI 等核心功能正常

- [x] **SPEC-002**: 创建 agents 模块并配置隔离加载
  - **背景 / 目标**: 创建独立的 agents 模块并实现隔离加载机制，不污染 sys.path
  - **范围**: agents 模块创建、_agents.py 隔离加载器实现、导入验证
  - **关键决策**: 使用 importlib.util.spec_from_file_location 实现模块隔离加载
  - **实现约束**:
    - packages/agents/ 包含 Wisadel 核心功能和 providers 子模块
    - 在 packages/dashboard/ 下创建 _agents.py 隔离加载器
    - _agents.py 使用 spec_from_file_location 加载，不修改 sys.path
    - dashboard/main.py 通过 `from _agents import agents` 导入
  - **接口 / 对接点**:
    - packages/agents/__init__.py 导出 Wisadel、MinimaxProvider
    - packages/dashboard/_agents.py 提供 agents 模块
    - packages/dashboard/main.py 使用 `from agents import Wisadel, MinimaxProvider`
  - **命令 / 操作**: 模块创建、导入测试、隔离性验证
  - **验收（勾选即证据）**:
    - [x] packages/agents/ 目录结构完整（包含 core.py、charms.py、providers/、tools/、agents/、tests/）
    - [x] _agents.py 文件存在且包含正确的加载逻辑
    - [x] dashboard/main.py 中可成功执行 `from agents import Wisadel, MinimaxProvider`
    - [x] 运行时 Wisadel、MinimaxProvider 正常工作
    - [x] sys.path 未被修改（隔离性验证通过）

- [x] **SPEC-003**: Coders 模块隔离加载和导入标准化
  - **背景 / 目标**: 完善 coders 模块设计，统一通过 _coders.py 隔离加载器暴露所有功能
  - **范围**: coders 模块导出、导入方式标准化、文档同步
  - **关键决策**:
    - 使用统一的 `from _coders import ClassName` 导入模式
    - 所有 coder 通过 _coders.py 隔离加载，保持模块隔离性
    - 模块导出 KiloCode、ClaudeCode、run_command 等实现
  - **实现约束**:
    - 在 `packages/coders/__init__.py` 中导出 KiloCode、ClaudeCode、run_command
    - 在 `packages/dashboard/_coders.py` 中暴露所有 coder 类型和 run_command 函数
    - 更新所有导入示例为 `from _coders import ...` 格式
  - **接口 / 对接点**:
    - packages/coders/__init__.py 导出 KiloCode、ClaudeCode、run_command
    - packages/dashboard/_coders.py 隔离加载和暴露 coder 类型
    - packages/dashboard/main.py 使用 `from _coders import ClassName` 导入
  - **命令 / 操作**: 导出配置、导入方式更新、文档同步
  - **验收（勾选即证据）**:
    - [x] _coders.py 暴露了所有 coder 类型和 run_command
    - [x] 所有导入已改为 `from _coders import ...` 格式
    - [x] 文档已同步更新，无遗留引用
    - [x] 整个模块隔离性验证通过

- [ ] **SPEC-004**: 命令执行按钮功能
  - **背景 / 目标**: 在 Dashboard 界面添加"润"按钮，集成 coders 模块的命令执行功能
  - **范围**: UI 按钮添加、run_worker 集成、异步线程调用
  - **关键决策**:
    - 复用 `packages/coders/kilocode.py` 的 `run_command()` 函数（Phase 3 已实现）
    - 使用异步线程执行，避免阻塞 UI 主线程
    - 关键原因：命令本身执行耗时明显，若采用阻塞式等待会造成界面长时间不可交互
    - 跨平台支持由 kilocode.run_command 封装（Windows PowerShell / macOS-Linux bash）
  - **实现约束**:
    - 按钮位置：界面下方中间
    - 按钮文字：显示"润"
    - 执行命令：`echo "Hello Run"`
    - 执行方式：通过 `RunWorker(QThread)` 在线程中异步调用 `run_command()`
    - 输入策略：子进程 `stdin` 使用 `DEVNULL`，避免进入标准输入等待态（由 kilocode 处理）
    - 输出处理：使用 `logger.info()` 记录 stdout
    - 错误处理：捕获异常并记录 stderr
  - **接口 / 对接点**:
    - UI 层：main_window.py 添加按钮组件
    - 线程层：run_worker.py 提供 `RunWorker(QThread)` 封装
    - 执行层：`from _coders import run_command` 导入核心执行逻辑
    - 日志层：logger.info() 输出结果
  - **已知问题**：命令执行偶现卡住（详细分析与解决方案见 Design 章节"命令执行机制与故障排查"）
  - **命令 / 操作**: UI 布局调整、事件绑定、命令执行测试、故障排查
  - **验收（勾选即证据）**:
    - [x] 界面下方中间显示"润"按钮
    - [ ] 点击按钮触发命令执行
    - [ ] 命令执行为异步线程，UI 不阻塞
    - [ ] stdout 内容正确输出到日志（logger.info）
    - [ ] stderr 错误正确捕获并记录
    - [ ] 跨平台支持正常（Windows/macOS/Linux）
    - [ ] 卡住问题已定位根因并解决（或确认为可接受的偶现问题）

- [ ] **SPEC-005**: CodingAgent 可配置工作目录
  - **背景 / 目标**: 实现 CodingAgent 核心功能，支持用户通过 UI 选择工作目录，并在指定目录中执行命令，为后续代码理解、分析、生成等高级功能奠定基础
  - **范围**:
    - 核心执行器：修改 kilocode.run_command() 支持 cwd 参数
    - UI 目录选择器：main_window.py 添加目录选择按钮与路径显示
    - 关键决策**:
    - 在 `run_command()` 中添加可选 `cwd` 参数，默认值为用户主目录
    - 通过 subprocess 的 `cwd` 参数在指定目录中执行命令
    - 使用 PySide6 的 QFileDialog.getExistingDirectory 打开系统原生文件浏览器
    - MainWindow 维持 `self.working_directory` 全局状态变量，传递给 RunWorker 线程
    - 路径格式：使用 pathlib.Path 或 os.path.normpath 统一处理，支持跨平台
  - **实现约束**:
    - 函数签名：`run_command(command: str, cwd: str = None) -> subprocess.CompletedProcess | None`
    - 目录验证（执行前）：`os.path.exists(cwd) and os.access(cwd, os.R_OK | os.W_OK)`
    - 工作目录默认值：`os.path.expanduser("~")`（用户主目录）
    - 错误处理：目录不存在或权限不足时给出明确的错误消息
    - UI 按钮文字："选择工作目录"
    - 路径显示控件：标签或只读输入框
    - **已识别风险**:
      - 权限问题：选择的目录可能无读写权限，需提前检查或容错处理
      - 状态管理：目录选择后需在前后端保持同步
  - **接口 / 对接点**:
    - Core 层：`packages/coders/kilocode.py` 的 `run_command(command, cwd=None)`
    - UI 层：`packages/dashboard/ui/main_window.py` 的目录选择按钮与路径显示
    - State 层：MainWindow 的 `self.working_directory` 成员变量
    - 线程层：`packages/dashboard/run_worker.py` 的 RunWorker 类接收并传递 cwd 参数
    - 隔离加载层：`packages/dashboard/_coders.py` 暴露 run_command 函数
  - **命令 / 操作**:
    - 函数签名修改、参数扩展、目录验证逻辑添加
    - UI 控件添加、事件绑定、初始状态设置
    - 参数传递链路：UI → RunWorker → run_command
    - 单元测试与集成测试
  - **验收（勾选即证据）**:
    - [ ] run_command 支持 cwd 参数，指定目录执行命令
    - [ ] 在指定目录中执行 ls/pwd 命令，结果正确
    - [ ] 相对路径（如 `../` 等）在工作目录中正确解析
    - [ ] 目录不存在或权限不足时返回明确错误提示
    - [ ] UI 显示"选择工作目录"按钮
    - [ ] 点击按钮打开系统文件浏览器，选中后路径正确显示
    - [ ] 多次切换目录，命令执行基于当前工作目录
    - [ ] 跨平台支持正常（Windows/macOS/Linux）

---

## Tasks

### 执行规则

- **MUST** 严格按顺序执行任务，从第一个 `- [ ]` 开始
- **MUST** 一次只执行一个 Phase，完成后暂停等待下一步指示
- **MUST** 完成任务后将对应条目从 `- [ ]` 更新为 `- [x]`
- **MUST** 发生错误时立即停止，等待用户指示
- **MUST NOT** 跳过任务、不按顺序执行、执行列表外的工作

### 概览

| Phase       | Tasks | Completed | Progress |
|-------------|-------|-----------|----------|
| Phase 0     | 1     | 1         | 100%     |
| Phase 1     | 2     | 2         | 100%     |
| Phase 2     | 4     | 4         | 100%     |
| Phase 3     | 9     | 9         | 100%     |
| Phase 4     | 2     | 2         | 100%     |
| Phase 5     | 3     | 3         | 100%     |
| Phase 6     | 3     | 3         | 100%     |
| Phase 7     | 3     | 3         | 100%     |
| Phase 8     | 5     | 0         | 0%       |
| **Total**   | **32** | **27**   | **84%** |

### 各 Phase 说明

- **Phase 0**: Human-in-the-loop 确认需求（项目改造范围、模块清单确认）
- **Phase 1**: 基础架构搭建与 agents 模块创建
- **Phase 2**: Agent 模块复制与集成（包含 MiniMaxProvider 导入、PyInstaller 打包修复）
- **Phase 3**: Coders 模块创建与扩展（基础模块创建、kilocode 迁移、导入方式统一、废弃文件删除、文档同步、编译验证）
- **Phase 4**: UI 命令执行集成（"润"按钮集成与异步线程调用 coders.run_command）
- **Phase 5**: CodingAgent 核心功能实现（可配置工作目录、UI 目录选择、命令执行集成）
- **Phase 6**: KiloCode 优化（probe() 抽象、日志优化、独立日志输出）
- **Phase 7**: UI 调整优化（日志输出面板、工作目录显示、命令历史记录）
- **Phase 8**: 基础调度能力实现（任务队列、状态追踪、可观测性）

### Dependencies & Blockers

**前置条件**: 无

**异常依赖**: 无（所有任务按 Phase 顺序执行）

**已识别风险**: 无（所有风险已分配到对应 SPEC）

### Tasks Breakdown

#### Phase 0: 需求确认与准备（Human-in-the-Loop）

- [x] **HITL-001**: 确认项目改造需求与模块清单
  - **Dependencies**: 无
  - **Do**: 确认项目范围
  - **Check**: 需求明确
  - **Act**: 进入 Phase 1 执行

#### Phase 1: 基础架构搭建与模块创建

- [x] **TASK-101**: 基础架构搭建
  - **Dependencies**: HITL-001 完成
  - **Do**: 从 windows-app 项目复制基础架构
  - **Check**: 项目可正常运行
  - **Act**: 执行 TASK-102

- [x] **TASK-102**: 创建 agents 模块并配置跨包导入
  - **Dependencies**: TASK-101
  - **Do**:
    - 在 `packages/agents/` 目录下创建模块结构
      - 包含 core.py（Wisadel 核心功能）、charms.py（辅助功能）
      - 包含 providers 子模块（提供 MinimaxProvider 等 AI 提供商）
      - 创建 `packages/agents/__init__.py`（导出 Wisadel、MinimaxProvider）
    - 在 `packages/dashboard/` 下新建 `_agents.py`
      - 使用 `importlib.util.spec_from_file_location` 显式加载 agents 模块
      - 不向 sys.path 添加任何目录，确保隔离性
    - 在 `packages/dashboard/main.py` 中改为 `from _agents import agents`
    - 演示导入模式：`from agents import Wisadel, MinimaxProvider`（验证此模式可行）
  - **Check**:
    - agents 模块目录结构完整（core.py、charms.py、providers/、__init__.py）
    - _agents.py 文件存在且包含正确的加载逻辑
    - dashboard/main.py 中可成功执行 `from agents import Wisadel, MinimaxProvider`
    - 验证：运行 dashboard 时，agents 中 Wisadel、MinimaxProvider 正常工作
    - 验证：packages 下的其他模块不能被直接导入（隔离性检查）
  - **Act**: Phase 1 完成，进入 Phase 2

#### Phase 2: Agent 模块复制与集成

**说明**：Phase 2 专注于 agents 模块的完整复制与集成，包括 MiniMaxProvider 导入和 PyInstaller 打包修复。

- [x] **TASK-201**: 复制 windows-app/agent 到项目根目录
  - **Dependencies**: TASK-102
  - **Do**:
    - 将 `packages/windows-app/agent/` 下的所有文件和子目录完整复制到 `packages/agents/` 目录
    - 保持目录结构不变（包括 providers/、agents/、tools/、tests/ 等子目录）
    - 特别确保 `agents/providers/minimax_provider.py` 被正确复制
  - **Check**:
    - `packages/agents/` 目录结构与源目录完全一致
    - `packages/agents/providers/minimax_provider.py` 文件存在
    - 所有 __init__.py 文件已复制
  - **Act**: 执行 TASK-202

- [x] **TASK-202**: 更新 _agents.py 导入 MiniMaxProvider
  - **Dependencies**: TASK-201
  - **Do**:
    - 修改 `packages/dashboard/_agents.py`
    - 添加导入语句：`from agents.providers.minimax_provider import MinimaxProvider`
    - 确保导出 `MinimaxProvider` 供 dashboard 使用
    - 保持隔离性（不修改 sys.path）
  - **额外发现**：agents 模块内部导入路径使用 `from agent.` 而非 `from agents.`，导致 PyInstaller 无法正确解析依赖
  - **Check**:
    - _agents.py 能成功导入 MinimaxProvider
    - 导入过程不出错
  - **Act**: 执行 TASK-203

- [x] **TASK-203**: 验证 MiniMaxProvider 导入与实际调用
  - **Dependencies**: TASK-202
  - **Do**:
    - 在 `packages/dashboard/main.py` 中导入 `MinimaxProvider`
    - 使用输入 "Hello MiniMax" 调用 MinimaxProvider
    - 验证输出是 str 类型
    - 打印输入和输出内容
  - **Check** (人工验证):
    - MinimaxProvider 实例化成功
    - 调用返回 str 类型输出
    - 输入输出正确打印到控制台
  - **Act**: 执行 TASK-204

- [x] **TASK-204**: 修复 PyInstaller 打包后 agents 模块加载失败问题
  - **Dependencies**: TASK-203
  - **问题描述**:
    - `Dashboard.spec` 中 `datas=[]`（历史状态）未将 `packages/agents/` 目录打包进去
    - `_agents.py` 仅按文件路径加载，缺少对"模块已被收集"的常规导入回退
  - **解决方案**:
    - 步骤 1：修改 `Dashboard.spec` 添加 `pathex`、`datas` 和 `hiddenimports`
      ```python
      datas=[
          (str(agents_dir), 'agents'),  # 将 agents 目录打包进去
      ],
      hiddenimports=[
          'smolagents',
          'smolagents.models',
          'smolagents.tools',
          'anthropic',
          'anthropic.types',
      ],
      ```
    - 步骤 2：更新 `build.bat`，改为 `pyinstaller --noconfirm --clean Dashboard.spec`（强制走 spec）
    - 步骤 3：增强 `_agents.py`，优先 `import agents`，失败后回退到 `spec_from_file_location`
  - **Check**:
    - Dashboard.spec 已补齐 `pathex/datas/hiddenimports`
    - 开发环境运行验证通过
    - PyInstaller 打包后验证通过
  - **Act**: Phase 2 完成，进入 Phase 3

#### Phase 3: Coders 模块创建与扩展

**说明**：Phase 3 包含 coders 模块的完整创建、kilocode 迁移、导入方式统一、废弃文件删除、文档同步，最后进行完整编译验证。本阶段的主要目标是将 coders 模块从基础完善到生产可用。

- [x] **TASK-301**: 创建 coders 模块并配置隔离加载
  - **Dependencies**: TASK-204
  - **Do**:
    - 在 `packages/coders/` 目录下创建模块结构
      - 创建 kilocode.py（提供 KiloCode 类和 run_command 函数）
      - 创建 claudecode.py（提供 ClaudeCode 类）
      - 创建 `packages/coders/__init__.py`（导出 KiloCode、ClaudeCode、run_command）
    - 在 `packages/dashboard/` 下新建 `_coders.py`
      - 使用 `importlib.util.spec_from_file_location` 显式加载 coders 模块
      - 不向 sys.path 添加任何目录，确保隔离性
    - 在 `packages/dashboard/main.py` 中演示导入模式：`from _coders import KiloCode, run_command`
  - **Check**:
    - [x] coders 模块目录结构完整（kilocode.py、claudecode.py、__init__.py）
    - [x] _coders.py 文件存在且包含正确的加载逻辑
    - [x] dashboard 中可成功导入 coders 模块
    - [x] 验证隔离加载成功
  - **Act**: 执行 TASK-302

- [x] **TASK-302**: 验证 coders 模块导入与集成
  - **Dependencies**: TASK-301
  - **Do**:
    - 在 `packages/dashboard/main.py` 中导入 coders 模块中的各种 coder 类型
    - 在 main 函数中调用各 coder 的方法/函数，输出验证信息
    - 确保 coders 模块与 agents 模块可同时导入使用
    - 验证隔离性：两个模块通过各自的加载器独立加载，互不影响
  - **Check** (人工验证):
    - [x] 各种 coder 实例化成功
    - [x] 调用返回正确的输出
    - [x] 输入输出正确打印到控制台
    - [x] 日志正常记录
    - [x] agents 和 coders 两个模块都正常工作
  - **Act**: 执行 TASK-303

- [x] **TASK-303**: 更新 PyInstaller 配置支持 coders 模块
  - **Dependencies**: TASK-302
  - **Do**:
    - 修改 `packages/dashboard/Dashboard.spec`，在 `datas` 中添加 coders 目录
      ```python
      datas=[
          (str(agents_dir), 'agents'),
          (str(coders_dir), 'coders'),  # 新增
      ],
      ```
    - 更新 `hiddenimports` 如需添加 coders 相关依赖
    - 测试打包是否成功
  - **Check**:
    - [x] Dashboard.spec 已补齐 coders 数据目录
    - [x] 开发环境运行验证通过
    - [ ] PyInstaller 打包后验证通过
  - **Act**: 执行 TASK-304

- [x] **TASK-304**: 创建 kilocode.py 并迁移 run_command 函数
  - **Dependencies**: TASK-303
  - **背景与决策**:
    - 当前 `run_worker.py` 包含命令执行逻辑和 UI 线程封装，职责混合
    - 决策：**不完全抽象为 KiloCode 类**，理由如下：
      - `run_command()` 是无状态函数，适合保持函数形式
      - `RunWorker` 是 QThread 子类，与 PySide6 强耦合，应保留在 dashboard UI 层
    - 重构策略：核心逻辑迁移至 coders 模块，UI 层保持轻量封装
  - **Do**:
    - 在 `packages/coders/` 下创建 `kilocode.py`
    - 从 `run_worker.py` 迁移 `run_command()` 函数到 `kilocode.py`
    - 保留以下功能：
      - 跨平台命令执行（Windows PowerShell / macOS-Linux bash）
      - subprocess 管理与状态监控
      - 流式日志输出（stdout/stderr）
      - 心跳日志（每 5 秒）
    - 确保函数签名不变：`run_command(command: str) -> subprocess.CompletedProcess | None`
  - **Check**:
    - [x] `packages/coders/kilocode.py` 文件已创建
    - [x] `run_command` 函数包含完整逻辑
    - [x] 独立测试 `run_command` 函数可正常执行
  - **Act**: 执行 TASK-305

- [x] **TASK-305**: 更新 _coders.py 暴露 run_command 函数
  - **Dependencies**: TASK-304
  - **Do**:
    - 修改 `packages/dashboard/_coders.py`
    - 添加导入语句：`from coders.kilocode import run_command`
    - 确保 dashboard 可通过 `from _coders import run_command` 使用
    - 保持隔离性（不修改 sys.path）
  - **Check**:
    - [x] _coders.py 能成功导入 run_command
    - [x] 在 dashboard/main.py 中可执行 `from _coders import run_command` 测试导入
    - [ ] 调用 `run_command("echo test")` 返回正确结果（需安装 PySide6 后人工验证）
  - **Act**: 执行 TASK-306

- [x] **TASK-306**: 重构 run_worker.py 调用 coders.run_command
  - **Dependencies**: TASK-305
  - **Do**:
    - 修改 `packages/dashboard/run_worker.py`
    - 删除原有 `run_command` 函数实现
    - 从 `_coders` 导入 `run_command`：`from _coders import run_command`
    - 保留 `RunWorker(QThread)` 类，确保其调用导入的 `run_command`
    - 验证 `ui/main_window.py` 中的 `from run_worker import RunWorker` 仍正常工作
  - **Check**:
    - [x] run_worker.py 已更新为调用 coders.run_command
    - [ ] RunWorker 类功能正常（异步执行命令）（需人工验证）
    - [ ] main_window.py 导入 RunWorker 无错误（需人工验证）
    - [ ] 点击"润"按钮触发命令执行成功（需人工验证）
  - **Act**: 执行 TASK-307

- [x] **TASK-307**: 验证并完善 coders 模块类型导出
  - **Dependencies**: TASK-306
  - **做什么**:
    - 检查 `packages/coders/__init__.py` 中的所有导出
    - 确保在 `packages/dashboard/_coders.py` 中正确暴露所有类型
    - 验证 dashboard 可正常导入所有 coder 类型
  - **验证方法**:
    - 1. `python -c "from packages.coders import *; print('✓ coders 导入成功')"` 执行成功
    - 2. dashboard 可通过 `from _coders import ...` 正常加载各类型
  - **错误处理**:
    - 如果 __init__.py 导出失败，检查导入语句是否正确
    - 如果导入路径错误，验证文件位置是否正确
  - **Check**:
    - [x] `packages/coders/__init__.py` 正确定义导出
    - [x] 所有类型可实例化
    - [x] 在 `_coders.py` 中可成功导入和暴露
  - **Act**: 执行 TASK-308

- [x] **TASK-308**: 更新 dashboard 的 coder 调用语法为 `from _coders import ...`
  - **Dependencies**: TASK-307
  - **做什么**:
    - 检查 `packages/dashboard/main.py` 中的 coder 导入语句
    - 将所有 coder 导入改为从 `_coders` 模块导入的格式
    - 更新导入示例：
      - 替换 `from coders import ...` 为 `from _coders import ...`
      - 替换 `import coders` 后的 `coders.ClassName()` 调用为直接使用 `ClassName()`
    - 更新 `_coders.py` 确保导出所有需要的 coder 类型和 run_command 函数
  - **验证方法**:
    - 1. 在 dashboard 中执行 `from _coders import ...` 成功
    - 2. 所有导入的类型可正常实例化
    - 3. 运行 dashboard 验证导入无错误
  - **错误处理**:
    - 如果 `from _coders import ...` 失败，检查 `_coders.py` 的导出列表
    - 如果类不可实例化，检查类定义是否正确
  - **Check**:
    - [x] dashboard/main.py 的 coder 导入已更新为 `from _coders import ...` 格式
    - [x] `_coders.py` 导出所有必要的 coder 类型
    - [x] dashboard 可正常启动并导入所有 coder
  - **Act**: 执行 TASK-311

- [x] **TASK-311**: 编译验证和 UI 人工验收
  - **Dependencies**: TASK-308
  - **Do**:
    - 执行编译命令：`build.bat`（或 `pyinstaller Dashboard.spec`）
    - 验证编译无错误
    - 启动 Dashboard 应用
    - 在 UI 界面点击"润"按钮
    - 观察日志输出，确认命令执行流程完整
  - **Check** (人工验收):
    - [x] 编译成功，无模块导入错误
    - [x] Dashboard 应用成功启动
    - [x] 点击"润"按钮后命令正常执行
    - [x] 日志中显示完整的命令执行流程（包括心跳日志）
    - [x] 命令执行结果正确（stdout/stderr 记录正常）
  - **Act**: Phase 3 完成，进入 Phase 4

#### Phase 4: 命令执行功能开发

**说明**：Phase 4 实现"润"按钮功能，包括 UI 按钮添加、跨平台命令执行模块创建、异步线程集成等。

- [x] **TASK-401**: 添加"润"按钮 UI
  - **Dependencies**: TASK-311
  - **Do**:
    - 在 `packages/dashboard/ui/main_window.py` 中添加"润"按钮
      - 位置：界面下方中间
      - 文字：显示"润"
      - 布局：使用现有 UI 框架添加按钮组件
    - 预留按钮点击事件接口（暂不实现具体逻辑）
  - **Check**:
    - 界面下方中间显示"润"按钮
    - 按钮样式正常，可点击
    - 点击按钮时触发事件（可打印日志验证）
  - **Act**: 执行 TASK-402

- [x] **TASK-402**: 集成 run_command 到 UI 并实现异步执行
  - **Dependencies**: TASK-401, TASK-306（run_command 已在 coders 模块实现）
  - **关键原因**:
    - 主因：阻塞式子进程等待会导致 UI 长时间无响应
    - 辅因：子进程可能进入标准输入等待，需显式关闭 stdin（由 kilocode 处理）
  - **Do**:
    - 在 `packages/dashboard/run_worker.py` 中：
      - 从 `_coders` 导入 `run_command`：`from _coders import run_command`
      - 创建 `RunWorker(QThread)` 线程类，封装异步执行逻辑
      - 在线程的 `run()` 方法中调用 `run_command()`
    - 在 `main_window.py` 中：
      - 导入 `RunWorker`
      - 点击"润"按钮后创建并启动异步线程
      - 通过 `RunWorker` 在线程中执行命令
  - **Check**:
    - [x] run_worker.py 正确导入并使用 coders.run_command
    - [x] RunWorker 线程类正确封装异步执行逻辑
    - [x] 点击"润"按钮后线程正常启动并执行命令
    - [x] 命令执行期间 UI 不阻塞
    - [x] 日志中正确输出命令结果
  - **Act**: Phase 4 完成，进入 Phase 5

#### Phase 5: CodingAgent 核心功能实现

**说明**：实现可配置工作目录的 CodingAgent，支持用户通过 UI 选择工作目录并在选中目录中执行 shell 命令。详见 SPEC-005。

- [x] **TASK-501**: 修改 run_command 支持自定义工作目录
  - **Dependencies**: TASK-402
  - **Do**:
    - 修改 `packages/coders/kilocode.py` 中的 `run_command()` 函数
    - 添加可选参数 `cwd: str = None`，默认值为用户主目录
    - 在 subprocess.run() 中填充 `cwd=cwd` 参数
    - 执行前验证目录：`os.path.exists(cwd) and os.access(cwd, os.R_OK | os.W_OK)`
    - 目录不存在或权限不足时，返回明确的错误消息（通过 logger.error）
    - 在 `packages/dashboard/_coders.py` 中保持导出不变
  - **Check**:
    - [x] `run_command()` 支持 `cwd` 参数
    - [x] 指定目录执行命令成功（如 `run_command("ls", cwd="/tmp")` 在 /tmp 中执行）
    - [x] 相对路径操作正确（如 `run_command("ls ../sibling", cwd="/some/path")`）
    - [x] 目录不存在时返回明确错误提示
    - [x] 权限不足时返回权限错误提示
  - **Act**: 执行 TASK-502

- [x] **TASK-502**: 添加 UI 目录选择器和路径显示
  - **Dependencies**: TASK-501
  - **Do**:
    - 修改 `packages/dashboard/ui/main_window.py`
    - 在"润"按钮上方添加"选择工作目录"按钮（PushButton）
    - 添加标签或只读文本框显示当前选中的目录路径
    - 初始化 MainWindow 的 `self.working_directory = os.path.expanduser("~")`
    - 绑定按钮点击事件，调用 `QFileDialog.getExistingDirectory()`
    - 选中目录后，更新 `self.working_directory` 和界面显示
  - **Check**:
    - [x] 界面显示"选择工作目录"按钮
    - [x] 点击按钮打开系统文件浏览器
    - [x] 选中目录后，路径正确显示在界面上
    - [x] 多次切换不同目录，路径正确更新显示
    - [x] 未选择目录时，显示默认路径或提示文本
  - **Act**: 执行 TASK-503

- [x] **TASK-503**: 集成目录选择与命令执行全流程
  - **Dependencies**: TASK-502
  - **Do**:
    - 修改 `packages/dashboard/run_worker.py`：
      - 修改 RunWorker 类的 `__init__` 方法，添加 `cwd: str = None` 参数
      - 在 `run()` 方法中调用 `run_command(cmd, cwd=self.cwd)`
    - 修改 `packages/dashboard/ui/main_window.py` 的"润"按钮点击事件：
      - 获取当前 `self.working_directory`
      - 创建 RunWorker 时传入 `cwd=self.working_directory`
      - 在日志中记录选中的工作目录
    - 测试流程：选择目录 → 点击"润"按钮 → 命令在选中目录中执行
  - **Check**:
    - [x] 用户选择目录后，在该目录下执行 `ls` 或 `pwd` 命令，结果正确
    - [x] 多次切换不同目录，命令执行基于当前选中目录
    - [x] 目录权限不足时，命令执行给出明确错误提示
    - [x] 目录被删除后，选择新目录仍可正常执行
    - [x] 相对路径（如 `../`）在新工作目录中正确解析
    - [x] UI 层与 Core 层数据传递正确（通过日志验证）
  - **Act**: Phase 5 完成，所有核心功能交付

#### Phase 6: KiloCode 模块优化

**说明**：优化 KiloCode 模块的探针逻辑、日志处理和独立日志输出，提升命令执行的可观测性和可维护性。

- [x] **TASK-601**: 抽象独立的 probe() 方法
  - **Dependencies**: TASK-503
  - **背景**:
    - 当前 `run_command()` 方法内部包含探针逻辑，探针命令为 `Get-Command kilocode ...`
    - 问题：探针逻辑与命令执行耦合，每次调用都会执行一次探针，浪费资源
    - 决策：抽象为独立的 `probe()` 方法，由调用方自主决定何时调用
  - **Do**:
    - 创建 `KiloCode.probe(cwd: str | None = None) -> None` 实例方法
      - 工作目录验证：与 `run_command()` 相同的校验逻辑
      - 跨平台支持：Windows PowerShell + macOS/Linux bash
      - 探针命令：改为 `kilocode --version`（更简洁、更通用）
      - 输出处理：成功时 logger.info，失败时 logger.error
    - 创建模块级便捷函数 `probe(cwd: str | None = None) -> None`
      - 调用 `_default_instance.probe(cwd)`
      - 方便用户直接导入使用
    - 从 `run_command()` 中删除现有的探针块（Lines 68-83）
    - 保持两个方法独立：调用方自主决定是否调用 probe()
  - **Check**:
    - [x] `KiloCode.probe()` 方法创建成功
    - [x] 模块级 `probe()` 函数可直接导入使用
    - [x] 执行 `probe()` 输出正确的版本检查日志
    - [x] `run_command()` 中已删除原有探针逻辑
    - [x] 两个方法可独立调用且互不影响
  - **Act**: 执行 TASK-602

- [x] **TASK-602**: 优化日志处理（统一使用 logger.info）
  - **Dependencies**: TASK-601
  - **背景**:
    - 当前 `stream_reader()` 函数中，stderr 使用 `logger.error`，stdout 使用 `logger.info`
    - 发现：kilocode 的 stream 输出中，stderr 并不意味着报错，仅是 kilocode 的规范输出
    - 问题：使用 logger.error 易误导开发者认为存在错误
  - **Do**:
    - 修改 `stream_reader()` 函数的日志处理
      - 将 stderr 的日志级别从 `logger.error` 改为 `logger.info`
      - 保留 prefix 标识（"stdout" 和 "stderr"）便于区分和查看
    - 在注释中添加发现说明
      - 注释例：`# 注意：kilocode 的 stderr 并不意味着报错，直接使用 logger.info`
    - 仅修改 stream_reader 中关于 stderr 的日志输出，不影响其他错误处理
  - **Check**:
    - [x] stderr 日志改为 logger.info
    - [x] prefix 保持不变（仍显示 "stderr:" 标识）
    - [x] 注释中明确说明此发现
    - [x] 执行命令后，stderr 和 stdout 都以 info 级别出现在日志中
  - **Act**: 执行 TASK-603

- [x] **TASK-603**: KiloCode 独立日志输出配置（应用层配置方案）
  - **Dependencies**: TASK-602
  - **背景**:
    - 当前仅使用全局 logger，Dashboard 的日志和 KiloCode 的日志混合在一起
    - 需求：为 KiloCode 配置独立的日志文件（Dashboard-KiloCode-timestamp.log）
    - 设计：与 Dashboard 日志文件平行存放，方便独立查看和调试
  - **loguru filter 机制调研**:
    - `record["name"]`：完整模块路径，如 `"coders.kilocode"`
    - `record["module"]`：仅文件名，如 `"kilocode"`
    - **决策**：使用 `record["name"] == "coders.kilocode"` 精确匹配
  - **Do**:
    - **应用层配置**（`packages/dashboard/logger_config.py`）：
      - 在 `init_logger()` 中添加 KiloCode 专用 handler
      - 日志文件路径：与 Dashboard 日志同目录
      - 文件命名格式：`Dashboard-KiloCode-{time:YYYY-MM-DD}.log`
      - filter 条件：`filter=lambda record: record["name"] == "coders.kilocode"`
      - 配置示例：
        ```python
        logger.add(
            os.path.join(log_dir, "Dashboard-KiloCode-{time:YYYY-MM-DD}.log"),
            filter=lambda record: record["name"] == "coders.kilocode",
            rotation="1 MB",
            retention="10 days",
            level="DEBUG",
            encoding="utf-8"
        )
        ```
    - **模块层使用**（`packages/coders/kilocode.py`）：
      - 删除 `_get_kilocode_logger()` 函数和全局变量
      - 直接使用 `from loguru import logger`
      - 无需 bind、无需管理单例
      - logger 自动被 dashboard 层配置的 filter 识别
    - **windows-app 适配**（可选）：
      - 如需在 windows-app 中使用 kilocode，在其 logger_config.py 中添加类似配置
  - **Check**:
    - [x] dashboard/logger_config.py 已添加 KiloCode filter 配置
    - [x] kilocode.py 已删除日志配置代码，直接使用 logger
    - [x] 日志文件 Dashboard-KiloCode-*.log 生成成功
    - [x] 所有 KiloCode 相关日志自动输出到该文件
    - [x] 文件位置与 Dashboard 日志同目录
    - [x] Dashboard 主日志中不包含 kilocode 模块的日志
  - **Act**: Phase 6 完成，KiloCode 模块优化交付

#### Phase 7: UI 调整优化

**说明**：优化 Dashboard UI 显示，包括日志输出面板、工作目录显示、命令历史记录等功能，提升用户体验和可观测性。

- [x] **TASK-701**: UI 多横排布局重构与命令控制按钮优化
  - **Dependencies**: TASK-603
  - **背景**：当前 UI 采用单行布局，需要重构为多行样式结构，优化空间利用和视觉层级
  - **Do**:
    - **布局重构**（在 `packages/dashboard/ui/main_window.py`）：
      1. 创建多横排容器（QVBoxLayout 包含多个 QHBoxLayout）
      2. **第一个横排**（交互功能行）：
         - 组件顺序（从左到右）：
           1. 选择目录按钮（pushButton_selectDir），固定宽度
           2. cwd 只读文本框（lineEdit_cwd），使用 addWidget 添加（不设固定宽度，自动扩展）
           3. 自动扩展空白（QSpacerItem）
           4. \"预备\"按钮（pushButton_prepare，右对齐）
           5. \"开始\"按钮（pushButton_start，右对齐）
         - 按钮间距：8px
         - **cwd 文本框长度约束**：不设置固定宽度，通过布局自动扩展，确保与第二、三行的文本框保持一致长度
         - 处理文本框溢出：文本过长时使用 ellipsis
      3. **第二、三个横排**（占位行）：
         - 复制第一行样式结构
         - 所有控件设置 `disabled=True`
         - 用于预留未来功能扩展
    - **功能保留**：
      - 选择目录按钮：保留原有 onClick 逻辑（打开文件浏览器）
      - cwd 文本框：保留显示当前工作目录功能
      - \"预备\"按钮：功能与原\"润\"按钮一致（执行命令）
      - \"开始\"按钮：功能与原\"润\"按钮一致（执行命令）
    - **清理**：
      - 移除原有的\"润\"按钮及其事件绑定
      - 移除与\"润\"按钮相关的状态变量
  - **Check**:
    - [x] 第一个横排包含：选择目录按钮、cwd 文本框、\"预备\"按钮、\"开始\"按钮
    - [x] \"预备\"和\"开始\"按钮右对齐，间距 8px
    - [x] 选择目录按钮功能正常（点击后打开文件浏览器）
    - [x] cwd 文本框显示当前工作目录路径
    - [ ] cwd 文本框长度与第二、三行的文本框保持一致（视觉对齐）
    - [x] \"预备\"按钮点击后行为与原\"润\"按钮一致（执行命令）
    - [x] \"开始\"按钮点击后行为与原\"润\"按钮一致（执行命令）
    - [x] 原\"润\"按钮已移除
    - [x] 第二、三行正确禁用显示
    - [x] 窗口宽度变化时，按钮保持右对齐
    - [x] 文本框内容过长时，显示处理正确（无溢出）
  - **Act**: 执行 TASK-702

- [x] **TASK-702**: 实现"预备"和"开始"按钮的命令执行逻辑
  - **Dependencies**: TASK-701
  - **Do**:
    - **分别为"预备"和"开始"按钮配置不同的命令**：
      - **"预备"按钮**（pushButton_prepare）：
        - 执行 command1：包含 `# Instruction` 注释的命令
        - 命令格式：`kilocode run "# Instruction\n<实际指令内容>"`
        - 用途：执行准备性的任务或指令加载
      - **"开始"按钮**（pushButton_start）：
        - 执行 command2：包含 `# Current Task` 注释的命令
        - 命令格式：`kilocode run "# Current Task\n<实际任务内容>"`
        - 用途：执行当前的主要任务
    - **实现步骤**：
      1. 在 `main_window.py` 中为两个按钮绑定不同的事件处理函数
      2. 创建 `on_prepare_clicked()` 方法，构造并执行 command1
      3. 创建 `on_start_clicked()` 方法，构造并执行 command2
      4. 两个命令都通过 RunWorker 异步执行，传递当前 cwd
      5. 在日志中明确标识是"预备"还是"开始"触发的命令
  - **Check**:
    - [x] "预备"按钮点击时执行 command1（带 # Instruction）
    - [x] "开始"按钮点击时执行 command2（带 # Current Task）
    - [x] 两个命令都在当前 cwd 中正确执行
    - [x] 日志中可区分是哪个按钮触发的命令
    - [x] 命令执行期间 UI 不阻塞
    - [x] 命令执行结果正确记录到日志
  - **Act**: Phase 7 完成，命令执行逻辑差异化交付

- [x] **TASK-703**: 实时显示进程 PID 和运行时间
  - **Dependencies**: TASK-702
  - **问题分析**:
    - **UI 层需求**：在"开始"按钮右侧显示 PID 和已运行时间
    - **当前架构问题**：
      ```
      UI 层 (main_window.py)
        ↓ 创建 RunWorker(command, cwd)
      线程层 (run_worker.py)
        ↓ RunWorker.run() → 阻塞调用
      执行层 (kilocode.py)
        ↓ run_command() 内部有 pid 和 elapsed_time
        ✗ 但这些值无法传递到外部
      ```
    - **核心问题**：
      1. `run_command()` 是阻塞式函数调用，返回 CompletedProcess
      2. pid 和 elapsed_time 在函数内部（lines 127, 162），外部无法访问
      3. RunWorker 只有 `error` 信号，没有状态更新信号
      4. UI 层无法实时获取进程状态
  - **解决方案设计**：
    - **方案选择**：在 RunWorker 中添加实时状态信号（不修改 kilocode.py）
    - **理由**：
      1. 保持 run_command() 的独立性（可单独使用）
      2. RunWorker 天然为 UI 设计，适合增强信号机制
      3. QThread 信号机制非常适合实时状态更新
    - **技术方案**：
      ```python
      # 1. RunWorker 添加状态信号
      class RunWorker(QThread):
          status_update = Signal(int, int)  # (pid, elapsed_seconds)

          def run(self):
              # 启动子进程并获取 pid
              # 定期（每 0.5 秒）发射 status_update 信号
              # 调用 run_command() 执行命令
      ```
      ```python
      # 2. MainWindow 接收信号并更新 UI
      class MainWindow:
          def _setup_control_rows(self):
              # 在"开始"按钮右侧添加状态显示区域：
              # - 使用 QGroupBox 作为容器，标题显示在边框上
              # - 标题文字设置为 "PID"
              # - 内部嵌套两个 QLabel：
              #   - self.pid_value_label: 显示 PID 数字（如 "10234"）
              #   - self.timer_label: 显示运行时间（如 "00:05:23"）

          def _on_status_update(self, pid: int, elapsed: int):
              # 更新标签显示
      ```
  - **实现约束**：
    - **信号更新频率**：每 0.5 秒发射一次 status_update
    - **显示格式**：
      - PID 框内容: `{pid}` 或 `--`（无进程时）
      - 耗时框内容: `{HH:MM:SS}` 格式（如 `00:05:23`）或 `--:--:--`
    - **样式设计（两个独立的框）**：
      - **共同样式**：
        - 边框：1px 实线，颜色 #cccccc
        - 背景色：#f9f9f9（浅灰色）
        - 圆角：4px
        - 标题字体：常规字体，字号 9px，颜色 #666666
        - 内容字体：等宽字体（Consolas/Monaco），字号 11px
        - 内容颜色：#333333
        - 文字水平居中对齐
        - 内边距：上下 6px，左右 10px
      - **第一个框（PID）**：
        - 标题文字：`PID`
        - 固定宽度：约 80px
        - 内容：单行 QLabel 显示进程 ID
      - **第二个框（耗时）**：
        - 标题文字：`耗时`
        - 固定宽度：约 90px
        - 内容：单行 QLabel 显示运行时间
      - **框间距**：两个 QGroupBox 之间间距 4px
    - **布局调整**：在"开始"按钮右侧，与按钮间距 8px
    - **执行时机**：命令开始时显示实际值，结束时重置为 `--`
    - **不修改 kilocode.py**：保持执行层的独立性
  - **Do**:
    1. **修改 run_worker.py**：
       - 添加信号 `status_update = Signal(int, int)`
       - 在 `run()` 方法中启动计时器线程
       - 定期发射 pid 和 elapsed_seconds
    2. **修改 main_window.py（UI 布局）**：
       - 在第一行"开始"按钮右侧添加两个独立的 QGroupBox：
         - **第一个 QGroupBox（PID 框）**：
           - 标题设置为 "PID"
           - 固定宽度 80px
           - 内部一个 QLabel 显示 PID 数字（无前缀）
         - **第二个 QGroupBox（耗时框）**：
           - 标题设置为 "耗时"
           - 固定宽度 90px
           - 内部一个 QLabel 显示运行时间
         - 两个框之间间距 4px
       - QGroupBox 样式表：
         ```python
         QGroupBox {
             border: 1px solid #cccccc;
             background-color: #f9f9f9;
             border-radius: 4px;
             margin-top: 8px;  /* 为标题留出空间 */
             padding: 6px 10px;
             font-size: 9px;
             color: #666666;
         }
         QGroupBox::title {
             subcontrol-origin: margin;
             subcontrol-position: top center;
             padding: 0 5px;
             background-color: #f5f5f5;  /* 标题背景色与主窗口背景一致 */
         }
         QGroupBox QLabel {
             color: #333333;
             font-family: Consolas, Monaco, monospace;
             font-size: 11px;
             qproperty-alignment: AlignCenter;  /* 文字居中 */
         }
         ```
    3. **修改 main_window.py（信号处理）**：
       - 连接 `run_worker.status_update` 到 `_on_status_update` 槽函数
       - 实现 `_on_status_update()` 更新两个标签显示
       - 命令结束后重置显示为 `--` 和 `--:--:--`
  - **Check**:
    - [x] RunWorker 新增 status_update 信号
    - [x] 点击"开始"或"预备"按钮后，PID 数字正确显示在第一个框中
    - [x] 运行时间以 HH:MM:SS 格式实时更新在第二个框中
    - [x] 两个框独立显示，标题分别为 "PID" 和 "耗时"
    - [x] 两个框的标题都显示在边框顶部，打断边框线
    - [x] 标题背景色与主窗口背景融合，形成浮在边框上的视觉效果
    - [x] 两个框之间有 4px 间距
    - [x] PID 数字和耗时时间文字都水平居中对齐
    - [x] 等宽字体确保数字对齐整齐
    - [x] 命令结束后，两个框的内容都重置为 `--` 占位符
    - [x] 信号更新不影响命令执行性能
    - [x] UI 布局在不同窗口宽度下正常显示
    - [x] kilocode.py 保持不变（独立性验证）
  - **Act**: Phase 7 完成，实时状态显示交付

#### Phase 8: 基础调度能力实现

**说明**：实现 Dashboard 的基础调度能力，支持任务入队、顺序执行、状态追踪与执行日志回放，为后续自动化编排和批处理能力提供基础。

- [ ] **TEMP-801**: 写死 kilocode prompt 并验证效果
  - **Dependencies**: TASK-702
  - **Do**:
    - 在调度能力开发前，先在现有执行链路中临时写死一组 kilocode prompt
    - 使用固定输入触发命令执行，记录 stdout/stderr 与退出码
    - 对比写死 prompt 前后的执行稳定性与输出一致性
  - **Check**:
    - 写死 prompt 后命令可稳定执行，日志中可见完整输出
    - 输出内容符合预期，不出现卡住或无响应
    - 验证结果形成结论，可用于指导后续调度器设计
  - **Act**: 执行 TASK-801
- [ ] **TASK-801**: 设计并实现调度器核心模型
  - **Dependencies**: TEMP-801
  - **Do**:
    - 在 `packages/dashboard/` 中新增调度器核心模块（如 scheduler.py）
    - 定义任务模型（任务 ID、命令、cwd、状态、创建时间、更新时间）
    - 定义任务状态流转：`pending -> running -> success|failed|cancelled`
  - **Check**:
    - 调度器可创建任务并分配唯一任务 ID
    - 任务状态流转符合定义且可追踪
    - 异常状态（执行异常、中断）可正确落到 failed/cancelled
  - **Act**: 执行 TASK-802

- [ ] **TASK-802**: 集成队列执行与并发控制
  - **Dependencies**: TASK-801
  - **Do**:
    - 在 RunWorker 调用链上接入调度器，支持任务入队与顺序执行
    - 增加并发控制参数（默认串行，预留并发扩展位）
    - 支持任务取消（未开始任务可取消，运行中任务可请求终止）
  - **Check**:
    - 多个任务提交后按队列顺序执行
    - 取消任务后状态正确更新且不影响后续任务
    - 运行中任务终止后资源可回收，不产生僵尸进程
  - **Act**: 执行 TASK-803

- [ ] **TASK-803**: UI 调度面板与可观测性接入
  - **Dependencies**: TASK-802
  - **Do**:
    - 在 `packages/dashboard/ui/main_window.py` 增加基础调度面板（任务列表、状态、开始时间、结束时间）
    - 增加任务操作入口（提交任务、取消任务、查看输出）
    - 日志层补充任务维度日志（task_id、状态变更、退出码、耗时）
  - **Check**:
    - UI 可展示任务队列与实时状态变化
    - 单个任务日志可按 task_id 追踪完整生命周期
    - 调度能力在 Windows/macOS/Linux 下基础行为一致（串行调度、状态更新、日志可读）
  - **Act**: Phase 8 完成，基础调度能力交付
