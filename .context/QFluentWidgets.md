# WWM UI 方案：QFluentWidgets 集成

> updated_by: Qoder - Claude-Sonnet-4
> updated_at: 2026-05-03 00:15:00

## 决策背景

WWM 需要一个成熟的、经过市场检验的 UI 设计系统。经过全面调研（详见对话记录），最终选定 **QFluentWidgets**（PyQt-Fluent-Widgets）。

**选择理由：**
- PySide6 Qt Widgets 生态中唯一的完整设计系统（180+ 组件）
- Microsoft Fluent Design 规范，视觉成熟度高
- 7.8K GitHub Stars，活跃维护
- 与现有 Qt Widgets 代码 100% 兼容（继承自标准 Qt 类）
- 内置主题系统（明/暗/跟随系统）、主题色自定义、FramelessWindow

**许可策略：**
- 社区版 GPLv3，WWM 当前为 MIT 非商业项目
- MVP 阶段内部使用不触发 GPL 分发条款，可直接使用
- 分发阶段三条退路：①买 $599 商业授权 ②改 MIT→GPLv3 ③替换 UI 库

**旧方案存档：** `.context/Design-Token.md` 为自建 Token 方案，保留参考，不再执行。

---

## 1. 安装

```bash
# PySide6 轻量版（推荐 MVP）
pip install PySide6-Fluent-Widgets

# 全功能版（含 Acrylic 毛玻璃效果）
pip install "PySide6-Fluent-Widgets[full]"
```

**注意：** 包的 import 名统一为 `qfluentwidgets`，不要同时安装 PyQt 版本。

---

## 2. 初始化

```python
# main.py 中，创建 QApplication 后立即调用
from qfluentwidgets import setTheme, setThemeColor, Theme

app = QApplication(sys.argv)

setTheme(Theme.AUTO)           # 跟随系统明暗
setThemeColor("#2563EB")       # 主题色（与 Design-Token.md 中的 accent 一致）
```

QFluentWidgets 初始化后，所有 QFluentWidgets 组件自动获得 Fluent Design 外观，无需手写 QSS。

---

## 3. 集成架构

### 3.1 核心变更点

WWM 的集成只需要改 **三层**：

```
层级 1: 入口初始化
  main.py → 添加 setTheme() + setThemeColor()

层级 2: 窗口系统替换
  main_window.py → QMainWindow 改为 FramelessWindow
  layout_window_title_bar.py → 删除（FramelessWindow 内置标题栏）

层级 3: 组件替换
  各 Builder/Container 文件 → QPushButton 改为 PushButton/PrimaryPushButton
                             QLineEdit 改为 LineEdit
                             QGroupBox 改为 CardWidget（可选）
```

### 3.2 不需要改的

- **所有布局代码**（QVBoxLayout, QHBoxLayout, addWidget, addStretch）— 不变
- **所有业务逻辑**（信号槽连接、状态管理、Worker 线程）— 不变
- **三列布局比例**（2:2:3）— 不变
- **容器文件的组装逻辑** — 不变

### 3.3 styles.py 的角色变化

QFluentWidgets 接管了大部分样式，`styles.py` 从"唯一视觉真相源"变为"补充样式源"：

- **删除**：现有的 COLORS、FONTS 字典和全局 QSS（被 QFluentWidgets 主题接管）
- **保留**：`apply_stylesheet(app)` 函数，但内容改为 QFluentWidgets 不覆盖的补充样式
- **新增**：QFluentWidgets 初始化调用（setTheme、setThemeColor）

---

## 4. 组件映射表

| 文件 | 当前组件 | → QFluentWidgets 组件 | 改动量 |
|------|---------|----------------------|--------|
| **main_window.py** | `QMainWindow` + `Qt.FramelessWindowHint` | `FramelessWindow` | 小 |
| **layout_window_title_bar.py** | 手写标题栏（QWidget+QPushButton+拖动逻辑） | FramelessWindow 内置 | 删除整个文件 |
| **layout_window_status_bar.py** | `QStatusBar` + 本地 setStyleSheet | `QStatusBar`（保留，补充样式） | 小 |
| **layout_transparent.py** | `QWidget` + paintEvent 自绘 | `SimpleCardWidget` 或 `CardWidget` | 中 |
| **directory_selector_builder.py** | `QPushButton` + `QLineEdit` | `PushButton` + `LineEdit` | 小 |
| **file_selector_builder.py** | `QPushButton` + `QLineEdit` | `PushButton` + `LineEdit` | 小 |
| **solo_runner_builder.py** | `QPushButton` + `QGroupBox` + `QLabel` | `PrimaryPushButton` + `CardWidget` | 小 |
| **runbook_*_container.py** | `QWidget` + `QVBoxLayout` | 不变（纯布局） | 无 |

### 4.1 组件替换规则

**按钮分级：**
```python
# Run 按钮 → PrimaryPushButton（蓝底白字，强调操作）
from qfluentwidgets import PrimaryPushButton
run_btn = PrimaryPushButton("Run")

# 文件/目录选择按钮 → PushButton（默认次要样式）
from qfluentwidgets import PushButton
select_btn = PushButton("选择")

# 标题栏最小化/关闭 → FramelessWindow 内置，不再手写
```

**输入框：**
```python
from qfluentwidgets import LineEdit
path_input = LineEdit()
path_input.setReadOnly(True)
path_input.setPlaceholderText("选择目录...")
```

**卡片容器（替代 LayoutTransparent）：**
```python
from qfluentwidgets import SimpleCardWidget
panel = SimpleCardWidget()
# 自动带圆角、浅色背景，无需 paintEvent
```

---

## 5. 本地样式清理

集成 QFluentWidgets 后，以下 5 处本地样式 **全部删除**：

| 位置 | 代码 | 原因 |
|------|------|------|
| `layout_window_title_bar.py:28` | `label.setStyleSheet("color: #1a1a1a")` | 文件整体删除 |
| `layout_window_title_bar.py:34` | `min_btn.setStyleSheet(...)` | 文件整体删除 |
| `layout_window_title_bar.py:41` | `close_btn.setStyleSheet(...)` | 文件整体删除 |
| `layout_window_title_bar.py:27` | `label.setFont(font)` | 文件整体删除 |
| `layout_window_status_bar.py:15` | `self.setStyleSheet("QStatusBar {...}")` | QFluentWidgets 主题接管 |

---

## 6. 迁移分阶段

### Phase 1: 最小可用（1-2 天）

目标：获得 Fluent Design 外观，最小改动。

```
✅ pip install PySide6-Fluent-Widgets
✅ main.py 添加 setTheme() + setThemeColor()
✅ 替换按钮：QPushButton → PushButton / PrimaryPushButton
✅ 替换输入框：QLineEdit → qfluentwidgets.LineEdit
✅ 删除 layout_window_status_bar.py 的 setStyleSheet
```

此阶段**不动窗口系统**，保持现有 FramelessWindowHint 方案。

### Phase 2: 窗口系统升级（1-2 天）

目标：用 QFluentWidgets 的 FramelessWindow 替代手写方案。

```
✅ main_window.py: QMainWindow → FramelessWindow
✅ 删除 layout_window_title_bar.py 整个文件
✅ 更新 main_window.py 的标题栏引用
✅ 测试拖动、最小化、最大化、关闭功能
```

### Phase 3: 面板容器升级（1 天）

目标：用 CardWidget 替代手绘 LayoutTransparent。

```
✅ layout_transparent.py: 自绘 QWidget → SimpleCardWidget
✅ 删除 paintEvent（3px 彩色边框）
✅ 调整三列间距（space-2 = 8px）
```

### Phase 4: 主题系统完善（可选）

```
☐ 支持明/暗主题切换（设置入口）
☐ 主题色可配置
☐ styles.py 精简为仅补充样式
```

---

## 7. QFluentWidgets 可用组件速查

以下是 WWM 可能用到的组件（按使用场景）：

### 基础控件
| 组件 | 用途 |
|------|------|
| `PushButton` | 次要按钮 |
| `PrimaryPushButton` | 主要操作按钮（Run） |
| `TransparentPushButton` | 无背景按钮 |
| `LineEdit` | 文本输入 |
| `SearchLineEdit` | 搜索框 |
| `TextEdit` / `PlainTextEdit` | 多行文本 |
| `CheckBox` | 复选 |
| `ComboBox` | 下拉选择 |
| `SpinBox` | 数值输入 |

### 容器与布局
| 组件 | 用途 |
|------|------|
| `SimpleCardWidget` | 轻量卡片（替代 LayoutTransparent） |
| `CardWidget` | 标准卡片 |
| `ElevatedCardWidget` | 带阴影卡片 |
| `FramelessWindow` | 无边框窗口 |

### 反馈与提示
| 组件 | 用途 |
|------|------|
| `InfoBar` | 操作反馈通知 |
| `ProgressBar` / `ProgressRing` | 进度指示 |
| `StateToolTip` | 状态提示 |
| `ToolTip` | 悬停提示 |

### 标签文字
| 组件 | 用途 |
|------|------|
| `TitleLabel` | 面板标题 |
| `SubtitleLabel` | 小标题 |
| `BodyLabel` | 正文 |
| `CaptionLabel` | 辅助文字 |

---

## 8. 与旧方案（Design-Token.md）的关系

| 方面 | 旧方案（自建 Token） | 新方案（QFluentWidgets） |
|------|-------------------|----------------------|
| 色彩系统 | 手写 9 级灰度 + 功能色 | QFluentWidgets 内置 Fluent Token |
| 排版系统 | 手写 6 级字号梯度 | TitleLabel/BodyLabel/CaptionLabel 等 |
| 间距系统 | 手写 4px 基准网格 | 组件内置间距 + 布局代码控制 |
| 按钮分级 | QSS 选择器 `[class="secondary"]` | PrimaryPushButton vs PushButton 类型区分 |
| 面板容器 | paintEvent 重写 | SimpleCardWidget/CardWidget |
| 窗口系统 | 手写 FramelessWindowHint | FramelessWindow 内置 |
| 主题切换 | 无 | setTheme(Theme.DARK/LIGHT/AUTO) |
| 维护成本 | 高（所有样式自己写） | 低（库维护，只写补充样式） |

**旧方案中仍有参考价值的部分：**
- 设计哲学（"内容即界面"三条规则）
- 三列布局比例（2:2:3）
- 间距规范（4px 基准网格）
- 组件交互设计（选择器组件的布局方式）

---

## 9. 风险

| 风险 | 缓解 |
|------|------|
| GPL 许可冲突 | MVP 阶段不分发，分发时买授权/改协议/替换库 |
| PySide6 版本兼容 | 集成前先验证 `pip install` 和基础运行 |
| 依赖体积增加 | QFluentWidgets 轻量版体积可控 |
| 自定义超出库能力 | QFluentWidgets 组件继承自标准 Qt 类，可子类化扩展 |
| 库停止维护 | 7.8K Stars + 活跃社区，短期风险低；长期可回退到自建 Token 方案 |

---

## 参考链接

- GitHub: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
- 文档: https://pyqt-fluent-widgets.readthedocs.io
- 官网: https://qfluentwidgets.com
- PyPI（PySide6 版）: https://pypi.org/project/PySide6-Fluent-Widgets/
