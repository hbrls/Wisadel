# WWM Design Token 定义

> updated_by: Qoder - Claude-Sonnet-4
> updated_at: 2026-05-02 22:58:00

## 设计哲学

**核心原则：内容即界面。**

UI 应该是隐形的。控件、边框、色块都应退到背景里，让用户的注意力完全留在内容和操作流上。层次感不靠颜色深浅和粗线条来表达，而是靠字号梯度、留白节奏和微妙的灰度变化来建立。

参考标杆：Linear（精致工具感）、Notion（内容驱动布局）、Things 3（呼吸感间距）。

**三条不可违背的规则：**
1. 如果一个元素可以没有边框，就不要边框
2. 如果一个颜色可以用灰度替代，就不用彩色
3. 如果一个效果可以靠间距解决，就不加阴影

---

## 1. 色彩系统

### 1.1 灰度主轴（所有 UI 骨架只用灰度）

| Token | 色值 | 用途 |
|-------|------|------|
| `gray-0` | `#FFFFFF` | 窗口底色、输入框底色 |
| `gray-50` | `#FAFAFA` | 面板底色、卡片背景 |
| `gray-100` | `#F5F5F5` | 悬停态底色、分割区域 |
| `gray-200` | `#E8E8E8` | 边框色（唯一允许的边框颜色） |
| `gray-300` | `#D4D4D4` | 禁用态边框 |
| `gray-400` | `#A3A3A3` | Placeholder 文字、禁用态文字 |
| `gray-500` | `#737373` | 次要文字（标签、说明） |
| `gray-600` | `#525252` | 正文文字 |
| `gray-900` | `#171717` | 标题文字、主要操作文字 |

### 1.2 功能色（仅在语义明确时使用）

| Token | 色值 | 用途 |
|-------|------|------|
| `accent` | `#2563EB` | 主按钮、选中态、进度条 |
| `accent-hover` | `#1D4ED8` | 主按钮悬停 |
| `accent-pressed` | `#1E40AF` | 主按钮按压 |
| `accent-light` | `#EFF6FF` | 选中行背景、轻强调 |
| `success` | `#16A34A` | 完成状态 |
| `error` | `#DC2626` | 错误状态、关闭按钮悬停 |
| `warning` | `#D97706` | 警告状态 |

### 1.3 透明度规则

**取消差异化透明度。** 三列面板统一使用 `gray-50`（#FAFAFA）纯色底，不用 alpha 通道。窗口本身保持 `WA_TranslucentBackground`（系统层圆角需要），但面板内部不做透明。

理由：差异化透明度是当前 UI 最大的视觉噪音来源。极简风格下，一致的浅灰底比复杂的半透明层更干净。

---

## 2. 排版系统

### 2.1 字体栈

| 平台 | 字体栈 |
|------|--------|
| Windows | `"Segoe UI Variable", "Segoe UI", system-ui, sans-serif` |
| macOS 开发环境 | `"SF Pro Text", -apple-system, system-ui, sans-serif` |
| 等宽 | `"Cascadia Code", "JetBrains Mono", Consolas, monospace` |

注：`Segoe UI Variable` 是 Windows 11 的新系统字体，支持可变字重，比 Segoe UI 更现代。在 Win10 上自动回退到 Segoe UI。

### 2.2 字号梯度

| Token | 字号 | 行高 | 字重 | 用途 |
|-------|------|------|------|------|
| `text-xs` | 11px | 16px | Regular (400) | 状态栏、时间戳 |
| `text-sm` | 12px | 18px | Regular (400) | 辅助说明、标签 |
| `text-base` | 13px | 20px | Regular (400) | 正文、输入框内容 |
| `text-md` | 14px | 22px | Medium (500) | 按钮文字、小标题 |
| `text-lg` | 16px | 24px | Semibold (600) | 面板标题 |
| `text-xl` | 18px | 28px | Semibold (600) | 窗口标题 |

### 2.3 层次规则

用字号和字重建立层次，而非颜色：
- **一级层次**：`text-lg` + `gray-900`（面板标题）
- **二级层次**：`text-md` + `gray-900`（按钮/小标题）
- **三级层次**：`text-base` + `gray-600`（正文）
- **四级层次**：`text-sm` + `gray-500`（说明文字）
- **五级层次**：`text-xs` + `gray-400`（辅助信息）

---

## 3. 间距系统

### 3.1 基准网格：4px

所有间距必须是 4 的倍数。

| Token | 值 | 用途 |
|-------|-----|------|
| `space-1` | 4px | 图标与文字之间、紧凑元素间 |
| `space-2` | 8px | 同组元素间距（label 与 input） |
| `space-3` | 12px | 组内元素间距 |
| `space-4` | 16px | 组与组之间、面板内边距 |
| `space-5` | 20px | 区块间距 |
| `space-6` | 24px | 大区块间距 |
| `space-8` | 32px | 面板间距、大留白 |

### 3.2 面板内边距

```
面板容器内边距：space-4（16px）四边统一
面板之间间距：space-2（8px）
标题栏高度：36px（当前 32px 偏紧，+4px）
状态栏高度：28px
```

### 3.3 三列布局

保持 2:2:3 比例不变。列与列之间用 `space-2`（8px）间隙分隔，不用边框。

---

## 4. 深度与边界

### 4.1 核心思路：用间距替代边框

| 场景 | 当前做法 | 新做法 |
|------|---------|--------|
| 三列面板分隔 | 3px 彩色边框 | 8px 间隙 + 背景色差（gray-50 vs gray-0） |
| 标题栏与内容分隔 | 无 | 1px `gray-200` 底线 |
| 状态栏与内容分隔 | 无 | 1px `gray-200` 顶线 |
| 组件内部分组 | 无 | 间距层级区分 |

### 4.2 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `radius-sm` | 4px | 按钮、输入框、小元素 |
| `radius-md` | 6px | 面板、卡片 |
| `radius-lg` | 8px | 窗口圆角（FramelessWindow） |

### 4.3 阴影（极度克制）

| Token | 值 | 用途 |
|-------|-----|------|
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | 仅用于浮动元素（下拉菜单、tooltip） |
| `shadow-md` | `0 2px 8px rgba(0,0,0,0.08)` | 仅用于窗口本身的系统级投影 |

原则：面板内部不用阴影。阴影只出现在"悬浮于内容之上"的元素。

---

## 5. 组件设计语言

### 5.1 按钮

**主按钮（Primary）**
```
背景：accent (#2563EB)
文字：#FFFFFF
圆角：radius-sm (4px)
内边距：8px 16px
字号：text-md (14px, Medium)
悬停：accent-hover (#1D4ED8)
按压：accent-pressed (#1E40AF)
禁用：背景 gray-200, 文字 gray-400
```

**次按钮（Secondary / Ghost）**
```
背景：transparent
文字：gray-600
边框：1px solid gray-200
圆角：radius-sm (4px)
悬停：背景 gray-100
按压：背景 gray-200
```

**关键设计决策**：Run 按钮用 Primary，文件/目录选择器按钮用 Secondary。减少蓝色按钮的泛滥，让真正需要行动的按钮突出。

### 5.2 输入框 / 文本框

```
背景：gray-0 (#FFFFFF)
边框：1px solid gray-200
圆角：radius-sm (4px)
内边距：8px 12px
字号：text-base (13px)
高度：32px
聚焦态：边框变 accent (#2563EB), 无 glow
只读态：背景 gray-50, 边框 gray-200
```

### 5.3 选择器组件（目录/文件选择器）

```
布局：[Secondary 按钮 80px] [space-2] [只读输入框 flex:1]
按钮宽度从 120px 缩至 80px（"选择" 两字足够）
输入框文字用等宽字体显示路径
溢出文本左截断，显示路径尾部（...docs/project/file.txt）
```

### 5.4 状态框

```
尺寸：自适应内容，最小 48x40px
标签：text-xs, gray-500, 顶部
数值：text-md, gray-900, 居中
无边框，用 gray-50 背景区分
```

### 5.5 标题栏

```
高度：36px
背景：gray-0 (#FFFFFF)
底部分割：1px solid gray-200
标题文字：text-md (14px), gray-900, 左侧 space-4 偏移
窗口控制按钮：
  - 尺寸：46x36px
  - 默认态：无背景，图标 gray-500
  - 悬停态：背景 gray-100
  - 关闭按钮悬停：背景 error (#DC2626)，图标 #FFFFFF
```

### 5.6 状态栏

```
高度：28px
背景：gray-50 (#FAFAFA)
顶部分割：1px solid gray-200
文字：text-xs (11px), gray-500
左边距：space-4 (16px)
```

---

## 6. 面板容器统一规范

### 6.1 取消当前的差异化设计

| 属性 | 当前 | 新规范 |
|------|------|--------|
| 背景透明度 | 左128/中128/右26 | 三列统一 gray-50 纯色 |
| 边框 | 3px green/red/blue | 无边框 |
| 圆角 | 无 | radius-md (6px) |
| 内边距 | 0 | space-4 (16px) |
| 列间距 | 0 | space-2 (8px) |

### 6.2 面板内部布局

```
面板标题行：text-lg + gray-900，底部 space-3 留白
选择器区域：底部 space-4 留白
Episode 列表：每个 episode 之间 space-3 留白
Run 按钮区域：顶部 space-5 留白，按钮 Primary 样式
```

### 6.3 三列之间的区分

不靠边框和颜色区分，靠标题文字区分。每列顶部有明确的面板标题（"Bootstrap" / "Task" / "WLoop"），字号 text-lg，这就是全部的区分手段。列与列之间 8px 间隙已足够建立边界。

---

## 7. 动效指南

### 7.1 原则：快且不打断

所有动效只服务于两个目的：确认操作已响应 + 引导注意力转移。不做装饰性动画。

### 7.2 时间规范

| Token | 时长 | 缓动 | 用途 |
|-------|------|------|------|
| `duration-fast` | 100ms | ease-out | 按钮状态切换、悬停反馈 |
| `duration-normal` | 200ms | ease-in-out | 面板展开/折叠 |
| `duration-slow` | 300ms | ease-in-out | 窗口出现/消失 |

### 7.3 Qt 实现方式

使用 `QPropertyAnimation` 对 `windowOpacity`、`geometry`、`minimumHeight` 等属性做动画。不建议对颜色做动画（Qt 颜色动画性能差）。

---

## 8. 实施架构：全局样式表 + 最小化局部修改

### 8.1 核心思路

Qt 的样式表支持级联：在 `QApplication` 上设置的样式表会自动传递到所有子 Widget。当前 `styles.py` 已有 `apply_stylesheet(app)` 函数做这件事，但覆盖范围不够全，导致各组件自行硬编码样式。

**方案：把 `apply_stylesheet()` 扩展为完整的全局主题引擎。** 所有视觉规则都在这一个函数里定义，组件文件不再包含任何样式代码。

实际上只需要改 **两类文件**：

1. **`styles.py`** — 定义 Token + 生成完整全局样式表（唯一的视觉真相源）
2. **少量布局文件** — 仅处理样式表无法控制的结构性改动（间距、透明度、边框绘制）

### 8.2 当前本地样式覆盖清单（需要清除的）

经过代码扫描，整个 `packages/wwm/ui/` 中只有 5 处本地 `setStyleSheet` 调用：

| 文件 | 代码 | 处理方式 |
|------|------|----------|
| `layout_window_title_bar.py:28` | `label.setStyleSheet("color: #1a1a1a")` | 删除，由全局样式表控制 |
| `layout_window_title_bar.py:34` | `min_btn.setStyleSheet(...)` | 删除，全局定义标题栏按钮样式 |
| `layout_window_title_bar.py:41` | `close_btn.setStyleSheet(...)` | 删除，全局定义关闭按钮样式 |
| `layout_window_status_bar.py:15` | `self.setStyleSheet("QStatusBar {...}")` | 删除，全局定义状态栏样式 |
| `layout_window_title_bar.py:27` | `label.setFont(font)` | 删除，全局字体定义覆盖 |

清除这些后，所有样式都来自一个源头。

### 8.3 全局样式表覆盖范围

`apply_stylesheet(app)` 需覆盖以下所有 Widget 类型：

```python
def apply_stylesheet(app):
    """一个函数，定义整个应用的视觉表现。"""
    stylesheet = f"""
    /* === 全局基础 === */
    QMainWindow {{ ... }}
    QWidget {{ font-family, font-size, color }}
    
    /* === 按钮分级 === */
    QPushButton {{ ... }}                    /* Primary 默认 */
    QPushButton:hover {{ ... }}
    QPushButton:pressed {{ ... }}
    QPushButton:disabled {{ ... }}
    QPushButton[class="secondary"] {{ ... }} /* Secondary/Ghost */
    
    /* === 输入框 === */
    QLineEdit {{ ... }}
    QLineEdit:read-only {{ ... }}
    QLineEdit:focus {{ ... }}
    
    /* === 标题栏 === */
    #titleBar {{ ... }}
    #titleBar QPushButton {{ ... }}          /* 窗口控制按钮 */
    #closeButton:hover {{ ... }}             /* 关闭按钮特殊悬停 */
    
    /* === 状态栏 === */
    QStatusBar {{ ... }}
    
    /* === 滚动条 === */
    QScrollBar:vertical {{ ... }}
    QScrollBar::handle:vertical {{ ... }}
    
    /* === 标签页 === */
    QTabWidget::pane {{ ... }}
    QTabBar::tab {{ ... }}
    
    /* === 标签文字层次 === */
    QLabel[class="title"] {{ ... }}
    QLabel[class="subtitle"] {{ ... }}
    QLabel[class="caption"] {{ ... }}
    """
    app.setStyleSheet(stylesheet)
```

Qt 支持通过 `objectName`（`#titleBar`）和 `property`（`[class="secondary"]`）做选择器，类似 CSS 的 id 和 class 选择器。组件只需设置 `setObjectName()` 或 `setProperty("class", "secondary")`，样式自动生效。

### 8.4 结构性修改清单（样式表管不到的）

全局样式表能控制颜色、字体、边框、圆角，但控制不了以下内容：

| 文件 | 改动 | 说明 |
|------|------|------|
| `layout_transparent.py` | 重写 `paintEvent()` | 去除 3px 彩色边框，改为 gray-50 纯色背景 + radius-md 圆角，不用 alpha |
| `main_window.py` | 三列 layout spacing 改为 8px | 增加列间隙，标题栏高度调整 |
| `layout_window_title_bar.py` | 删除所有 `setStyleSheet` 和 `setFont`，加 `setObjectName` | 标记 `#titleBar`、`#closeButton` 让全局样式表接管 |
| `layout_window_status_bar.py` | 删除本地 `setStyleSheet` | 全局样式表已覆盖 |
| 各 Builder/Container 文件 | 给按钮加 `setProperty("class", "secondary")` 或 `setObjectName` | 不改样式，只打标记，让全局样式表区分 Primary/Secondary |
