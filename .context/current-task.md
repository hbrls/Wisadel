# TASK-310: 接入 ALoop

> updated_by: Codex - GPT-5
> updated_at: 2026-05-25 14:39:07

## 背景

当前 `packages/wwm` 已有 `WLoop` 页面，左侧导航使用 `FIF.SYNC` 图标，并通过 `InfoBadge` 在导航图标上显示运行提示。`WLoop` 的业务编排位于 `packages/combos/wloop.py`，UI 执行容器位于 `packages/wwm/ui/containers/combo_wloop_container.py`。

本任务需要接入新的 `ALoop` 功能。第一阶段要求与 `WLoop` 保持结构相似，可以复制 `WLoop` 相关实现作为骨架，等待后续需求继续澄清后再修改业务细节。

## 需求澄清

1. 新增 `ALoop`，包括左侧导航新增入口、使用 Robot 图标、右侧新增页面，以及 `packages/combos` 中新增 `aloop`。
2. `ALoop` 基本代码结构与 `WLoop` 类似，第一版可以从 `WLoop` 复制。
3. `ALoop` 左侧导航图标需要 Badge 能力。
4. `ALoop` 右侧是 Run 区，并且固定提供三个 Tab：`Run 1`、`Run 2`、`Run 3`。
5. 三个 Tab 在页面初始化时就创建出来，不需要 `New Run` 按钮，不支持动态增删。
6. 用户通过切换 Tab 决定查看哪个 Run；App 只做显示和隐藏。
7. 隐藏 Tab 中的 Run 可以继续实际执行任务。
8. 三个 Run 之间必须隔离，互不干扰。
9. 左侧导航 Badge 数字应反映当前正在 Run 的 Tab 个数。
10. 正在 Run 的 Tab 个数不属于 `ALoop` 状态机，应由 Container 或 UI 结构持有和聚合。
11. 当前不同功能之间完全隔离，不做提前抽象；不要抽导航管理，不要把 `WLoop` 与 `ALoop` 合并成通用框架。

## 图标能力确认

`qfluentwidgets.FluentIcon` 中已确认存在 `ROBOT`：

```python
from qfluentwidgets import FluentIcon as FIF

FIF.ROBOT
```

因此 `ALoop` 左侧导航图标应使用 `FIF.ROBOT`。

## 总体设计

`ALoop` 应设计为一个独立功能切片：

```text
MainWindow
  └─ ALoopPage, FIF.ROBOT, "ALoop"
      └─ ComboALoopTabsContainer
          ├─ TabWidget
          │   ├─ Run 1 -> ComboALoopContainer(run_id="run-1")
          │   ├─ Run 2 -> ComboALoopContainer(run_id="run-2")
          │   └─ Run 3 -> ComboALoopContainer(run_id="run-3")
          └─ running_count_changed(int)
```

核心原则：

- 一个 `ComboALoopContainer` 表示一个完整独立的 Run。
- 每个 `ComboALoopContainer` 内部持有自己的 `ALoop()` 状态机实例、Worker、进度、按钮锁定状态和状态历史。
- `ComboALoopTabsContainer` 只负责创建三个 Container、放入 Tab、聚合运行数量。
- Tab 切换只影响可见性，不暂停、不销毁、不重置隐藏 Tab 中的任务。
- `running_count` 是 UI 聚合态，不写入 `combos.aloop.ALoop` 状态机。

## Domain 层设计

新增 `packages/combos/aloop.py`。

第一版从 `packages/combos/wloop.py` 复制，做最小命名替换：

- `WLoop` 改为 `ALoop`
- 状态 id 从 `wloop` 改为 `aloop`
- 日志前缀从 `[WLoop]` 改为 `[ALoop]`
- Episode component 从 `WLoopSoloEpisode` 改为 `ALoopSoloEpisode`

第一版状态机保持与 `WLoop` 相同的形态：

```text
IDLE -> aloop -> aloop -> ... -> FINISHED -> IDLE
```

每个 `ComboALoopContainer` 都创建自己的 `ALoop()`，因此三个 Run 的 `state`、`_count`、`reset()`、`next()` 完全隔离。

## UI 层设计

新增页面和容器：

- `packages/wwm/ui/pages/aloop_page.py`
- `packages/wwm/ui/containers/combo_aloop_tabs_container.py`
- `packages/wwm/ui/containers/combo_aloop_container.py`

`ALoopPage` 只负责挂载 `ComboALoopTabsContainer`。

`ComboALoopTabsContainer` 是 `ALoop` 专属 Tab 外壳：

- 使用 `qfluentwidgets.TabWidget`。
- 固定创建三个 `ComboALoopContainer`。
- Tab 标题固定为 `Run 1`、`Run 2`、`Run 3`。
- 监听三个子 Container 的运行状态变化。
- 重新计算正在运行的 Container 数量，并发出 `running_count_changed(int)`。

`ComboALoopContainer` 从 `ComboWLoopContainer` 复制，表示一个独立 Run：

- 持有一个 `ALoop()` 实例。
- 渲染工作目录选择、Episode 文件选择、Solo/Play 控制和状态历史。
- 自己管理 `_play_active`、Worker 生命周期和按钮锁定。
- 暴露 `is_running()`。
- 在运行状态变化时发出信号，供外层 Tab 容器重新统计。

## Tab 设计

`qfluentwidgets` 中已确认存在：

- `TabWidget`
- `TabBar`
- `Pivot`
- `SegmentedWidget`

本任务推荐使用 `TabWidget`，因为它天然表达“多个固定页面，当前显示一个”，最接近 Chrome Tab 的使用心智。

不使用 `Pivot` 或 `SegmentedWidget`，因为它们更适合同一页面内的视图切换，不适合表达多个并行任务实例。

## 并行执行语义

三个 Run 在页面初始化时全部创建，并长期存在：

- 用户在 `Run 1` 点击 Play 后，切到 `Run 2`，`Run 1` 继续执行。
- 用户可以在 `Run 2` 继续点击 Play，此时 `Run 1` 和 `Run 2` 可同时执行。
- `Run 3` 同理。
- 任意 Run 完成、失败、reset，只影响自己的 `ComboALoopContainer` 和自己的 `ALoop()`。

隐藏 Tab 中的 Worker 不应因 Tab 切换被暂停或销毁。

## Badge 设计

`ALoop` 左侧导航 Badge 数字表示当前正在运行的 Run 数量，范围为 `1` 到 `3`。当数量为 `0` 时隐藏 Badge。

责任划分：

```text
ComboALoopContainer
  - 暴露 is_running()
  - 在运行状态变化时发出 run_state_changed

ComboALoopTabsContainer
  - 监听三个子 Container
  - 每次重新计算 running_count = sum(c.is_running())
  - 发出 running_count_changed(count)

MainWindow
  - count == 0: 隐藏 ALoop badge
  - count > 0: 显示或更新 ALoop badge 文本为 str(count)
```

不要只靠 started/stopped 事件对整数做加减，因为异常、重复回调、状态恢复等情况可能导致计数漂移。更稳妥的方式是每次收到任意子 Container 的运行状态变化后，重新扫描三个 Container 的 `is_running()`。

该运行数量不进入 `packages/combos/aloop.py`，不属于 `ALoop` 状态机。

## MainWindow 接入

在 `MainWindow` 中新增独立的 `ALoop` 导航项：

```python
self.aloop_page = ALoopPage(self)
self.addSubInterface(
    self.aloop_page, FIF.ROBOT, "ALoop",
    position=NavigationItemPosition.TOP,
)
```

新增 `ALoop` 自己的 Badge 字段和显示/隐藏/更新逻辑。

注意：不要抽象通用导航 Badge 管理；`ALoop` 与 `WLoop` 保持功能隔离。

## 非目标

- 不改造 `WLoop`。
- 不抽通用 `ComboRunnerContainer`。
- 不抽通用导航 Badge manager。
- 不新增动态 Tab 创建能力。
- 不新增 Tab 关闭能力。
- 不把 running count 写入 Domain 状态机。
- 不在本任务中定义新的 ALoop 业务 workflow 细节，后续需求再澄清。

## 推荐落地顺序

1. 新增 `packages/combos/aloop.py`，复制并最小改名 `WLoop` Domain。
2. 新增 `ComboALoopContainer` 和 `ALoopSoloEpisode`，复制并最小改名 `ComboWLoopContainer`。
3. 新增 `ComboALoopTabsContainer`，固定创建三个 `ComboALoopContainer` 并放入 `TabWidget`。
4. 新增 `ALoopPage`。
5. `MainWindow` 接入 `ALoopPage`，使用 `FIF.ROBOT`。
6. `MainWindow` 增加 `ALoop` 专属数字 Badge 更新逻辑。
7. 后续再根据新需求调整 `ALoop` workflow、prompt、循环逻辑和错误策略。

## 人工验收

本任务涉及 UI 表现和交互语义，最终实现后需要人工验收：

- 左侧导航出现 `ALoop`，图标为 Robot。
- `ALoop` 页面出现固定三个 Tab：`Run 1`、`Run 2`、`Run 3`。
- 三个 Tab 各自拥有独立 Run 区。
- `Run 1` 执行时切到 `Run 2`，`Run 1` 仍继续运行。
- 三个 Run 可同时运行，互不影响。
- 左侧 `ALoop` Badge 数字正确反映正在运行的 Run 数量。
- 全部 Run 停止后，`ALoop` Badge 隐藏。

## 补充方案：Tab 与 Container 的缺口横线

> updated_by: Codex - GPT-5
> updated_at: 2026-05-25 15:42:21

### 问题

当前 `ALoop` 的 Tab 功能正常，但视觉归属不明显：当用户选中 `Run 1` 时，下方 Container 看起来只是一个普通执行区，不容易看出它对应的是 `Run 1`。

不采用“强化选中 Tab”的方向。需要让 Container 自己在视觉上与当前 Tab 建立连接。

### 目标效果

每个 `ComboALoopContainer` 顶部绘制一条横线，横线在对应 Tab 下方开一个缺口：

```text
[ Run 1 ] [ Run 2 ] [ Run 3 ]

────────────      ─────────────────────────
            gap
Container body...
```

切换到 `Run 1` 时，显示 `Run 1` 的 Container，缺口位于 `Run 1` Tab 下方。

切换到 `Run 2` 时，显示 `Run 2` 的 Container，缺口位于 `Run 2` Tab 下方。

切换到 `Run 3` 时同理。

### 关键约束

- 缺口横线的代码物理上必须在 `ComboALoopContainer` 内部。
- 不重写 `qfluentwidgets.TabWidget`。
- 不抽象到 `WLoop` 或通用导航管理。
- 不改变三个 Container 相互隔离的架构。
- Tab 仍然只是显示/隐藏页面；隐藏 Tab 中的 Run 继续执行。

### qfluentwidgets 能力确认

本地 `qfluentwidgets` 已确认提供：

- `TabWidget`
- `TabBar`
- `TabBar.tabRect(index)`
- `TabBar.tabRegion()`
- `setTabMinimumWidth(...)`
- `setTabMaximumWidth(...)`
- `setTabSelectedBackgroundColor(...)`
- `setTabShadowEnabled(...)`

但没有内置“Container 顶部横线在选中 Tab 下方开缺口”的样式能力。

因此推荐方案是：

```text
Tab 使用 qfluentwidgets.TabWidget
缺口横线由 ALoop 自己绘制
缺口位置使用 qfluentwidgets.TabBar.tabRect(index) 提供的真实几何
```

### 结构设计

维持当前结构：

```text
ALoopPage
  └─ TabWidget
      ├─ Run 1 -> ComboALoopContainer(run_index=0)
      ├─ Run 2 -> ComboALoopContainer(run_index=1)
      └─ Run 3 -> ComboALoopContainer(run_index=2)
```

在每个 `ComboALoopContainer` 顶部增加一个轻量绘制组件：

```text
ComboALoopContainer
  ├─ TabBridgeLine
  └─ 原有 Run UI
```

`TabBridgeLine` 只负责绘制横线和缺口，不负责状态机、worker、Tab 切换或运行数量统计。

### 几何数据流

`ALoopPage` 持有 `TabWidget`，因此由 `ALoopPage` 读取 Tab 的真实几何，并同步给三个 Container。

同步逻辑：

```text
for index, container in enumerate(run_containers):
    rect = tab_widget.tabBar.tabRect(index)
    container.set_tab_gap_geometry(
        gap_left=rect.left(),
        gap_width=rect.width(),
    )
```

`ComboALoopContainer` 只接收两个值：

- `gap_left`
- `gap_width`

Container 不直接依赖 `TabWidget`，也不读取其他 Container 状态。

### 为什么使用 tabRect

不要简单写死 `gap_left = tab_width * index`。

原因是 `qfluentwidgets.TabBar` 的真实布局会受到以下因素影响：

- `itemLayout` margin
- Tab 最小宽度
- Tab 最大宽度
- 是否 scrollable
- close button 显示模式
- shadow 和内部布局

`tabRect(index)` 是库布局完成后的真实 Tab 几何，优先使用它，避免后续样式变化导致缺口偏移。

### 绘制方式

推荐新增一个自定义 QWidget，例如 `TabBridgeLine`，在 `paintEvent` 中绘制两段线：

```text
左线：0 -> gap_left
右线：gap_left + gap_width -> widget.width()
```

中间不画线，即形成缺口。

线条样式建议：

- 高度：8 到 12px
- 颜色：使用现有 `COLORS["border"]`，或略深于 border 的中性灰
- 不做大 Header
- 不放文案
- 不做额外卡片

### 更新时机

需要在这些时机同步缺口几何：

1. `ALoopPage` 添加完三个 Tab 后。
2. Qt 布局稳定后，使用 `QTimer.singleShot(0, sync_gap_geometry)` 读取真实 `tabRect`。
3. `ALoopPage.resizeEvent` 后重新同步，避免窗口尺寸变化导致 Tab 几何变化。

未来如果改变 Tab 宽度、字体、关闭按钮、scrollable 配置，也应重新同步。

### 职责边界

`ComboALoopContainer`：

- 持有自己的 `ALoop()`。
- 持有自己的 Worker。
- 管理自己的运行状态。
- 发出自己的 `run_state_changed`。
- 绘制自己顶部的 `TabBridgeLine`。

`ComboALoopContainer` 不应该：

- 持有 running count。
- 管理 Tab 切换。
- 读取其他 Container 状态。
- 依赖 `WLoop`。
- 参与导航 Badge 管理。

`ALoopPage`：

- 管理 `TabWidget`。
- 创建三个 `ComboALoopContainer`。
- 使用 `tabBar.tabRect(index)` 同步缺口几何。
- 聚合三个 Container 的运行数量。

### 人工验收补充

- `Run 1` 页面顶部横线缺口对齐 `Run 1` Tab。
- `Run 2` 页面顶部横线缺口对齐 `Run 2` Tab。
- `Run 3` 页面顶部横线缺口对齐 `Run 3` Tab。
- 切换 Tab 后缺口位置正确变化。
- 调整窗口大小后缺口仍与 Tab 对齐。
- 缺口横线不影响三个 Run 的并行执行。
- 隐藏 Tab 中的 Run 仍能继续执行。
