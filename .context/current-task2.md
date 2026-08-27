# w-execute Run 导航重构方案

## 1. 背景与目标

`w-execute` 已从 `wwm` 中拆分为独立应用，目前只承载 WLoop 执行能力。现有界面仍沿用 WWM 的“功能导航 + 页面内 Tab”结构：左侧导航只有一个 `WLoop` 项，右侧 `WLoopPage` 再通过 `QTabWidget` 展示三个 Run。

本次调整的目标是让界面结构直接反映应用职责：

- 不再保留代表功能分类的左侧菜单。
- 复用左侧导航区域承载三个固定的 Run 入口。
- 移除右侧 `QTabWidget`，不再使用页面内 Run Tab。
- 固定提供 `Run 1`、`Run 2`、`Run 3` 三个 Run，不支持动态增删。
- 保留现有主 Run 状态监听方式，为每个 Run 提供 badge 效果。
- Solo 执行不参与 badge 和页面级运行状态统计。

## 2. 当前实现

```text
FluentWindow
├── 左侧 NavigationInterface
│   └── WLoop
│       └── WLoopPage
│           └── QTabWidget
│               ├── Run 1: ComboWLoopContainer
│               ├── Run 2: ComboWLoopContainer
│               └── Run 3: ComboWLoopContainer
└── StatusBar
```

当前 `WLoopPage` 已经创建三个独立的 `ComboWLoopContainer`，每个容器拥有自己的 `WLoop`、工作目录、Episode 控件、状态历史和主 Run 状态信号。当前缺少的是把这三个容器直接提升为窗口级导航页面。

`w-execute` 的现有 badge 逻辑位于 `ui/main_window.py`：页面汇总运行中的容器数量，通过 `InfoBadge.success` 将数量 badge 挂到 `WLoop` 导航项上。该逻辑来源于 `wwm`，但在新的导航结构中不再存在一个统一的 `WLoop` 导航项，因此需要改为逐个 Run 显示状态。

## 3. 目标结构

```text
FluentWindow
├── 左侧 NavigationInterface
│   ├── Run 1 [badge: 主 Run 运行时显示]
│   ├── Run 2 [badge: 主 Run 运行时显示]
│   └── Run 3 [badge: 主 Run 运行时显示]
└── StatusBar
```

每个导航项对应一个长期存活的页面实例：

```text
Run 1 页面
└── ComboWLoopContainer(run_id="run-1")

Run 2 页面
└── ComboWLoopContainer(run_id="run-2")

Run 3 页面
└── ComboWLoopContainer(run_id="run-3")
```

页面切换只改变当前可见页面，不重新创建或销毁 `ComboWLoopContainer`。因此切换 Run 时，其他 Run 的 worker、状态历史、表单值和执行状态都能保持不变。

## 4. 模块职责调整

### 4.1 `MainWindow`

- 继续负责窗口初始化、状态栏和导航注册。
- 删除代表单一功能的 `WLoop` 导航项。
- 创建并注册三个固定 Run 页面，建议使用稳定的 object name：`Run1Page`、`Run2Page`、`Run3Page`。
- 为每个 Run 页面连接其对应的 `ComboWLoopContainer.run_state_changed(bool)`。
- 为每个 Run 维护一个 badge 引用，避免重复创建 badge。
- 不再依赖 `WLoopPage.running_count_changed`，也不再显示“运行中总数”这一聚合 badge。

### 4.2 Run 页面组件

当前 `WLoopPage` 的职责是承载三个容器并提供右侧 Tab。重构后应改为“一个页面对应一个 Run 容器”的结构。页面组件只负责页面级组装，不复制执行逻辑。

推荐保留页面层，而不是让 `MainWindow` 直接把 `ComboWLoopContainer` 当作导航页面：

- 页面层明确隔离窗口导航和执行容器。
- 后续需要给 Run 页面增加标题、局部工具栏或页面级提示时，不需要改动 `ComboWLoopContainer`。
- `MainWindow` 只负责固定页面注册和状态连接，避免承担容器内部布局细节。

页面层可以采用专用于 WLoop 的轻量包装，例如 `WLoopRunPage`，构造时接收 `run_id` 并创建一个 `ComboWLoopContainer`。本次不抽取跨 ALoop/WLoop 的公共基类或通用页面，避免扩大改造范围。

### 4.3 `ComboWLoopContainer`

- 保持现有主 Run 执行逻辑、状态机和 `run_state_changed(bool)` 信号。
- 保持每个容器独立持有 `WLoop` 和 Episode 副本。
- 保持 `run_id`，用于页面实例识别和后续日志定位。
- 不新增 Solo 级别的运行状态信号。

## 5. Badge 设计

### 5.1 语义

badge 表示“对应 Run 的主 Play 流程正在执行”。它不是功能入口数量，也不是 Solo worker 数量。

| 状态 | 导航项 badge |
|------|--------------|
| 主 Run 未执行 | 隐藏 |
| 主 Run 执行中 | 显示绿色 `InfoBadge.success("1", ...)` |
| 主 Run 完成并 reset | 隐藏 |
| Solo 按钮执行 | 不变化 |

### 5.2 信号链

```text
ComboWLoopContainer.run_state_changed(bool)
    └── 对应 Run 页面/窗口回调
        ├── True  -> 显示对应导航项 badge
        └── False -> 隐藏对应导航项 badge
```

每个 Run 单独维护自己的 badge，Run 1 的状态不会改变 Run 2 或 Run 3 的 badge。badge 应通过导航组件的 `panel`、对应导航 widget 和 `InfoBadgePosition.NAVIGATION_ITEM` 创建，沿用 `wwm` 已验证的实现方式。

### 5.3 初始化与清理

- badge 初始为空，不在窗口启动时显示。
- 首次收到 `True` 时创建 badge；之后只更新显示状态，避免重复创建。
- 收到 `False` 时隐藏 badge，不销毁对象，以便下次运行复用。
- 如果导航 widget 尚未完成注册，不应创建 badge；连接关系应在 `addSubInterface` 完成后建立。

## 6. 导航与固定 Run 约定

- 导航项固定为三个，顺序始终为 `Run 1`、`Run 2`、`Run 3`。
- 使用稳定的页面 object name，建议为 `Run1Page`、`Run2Page`、`Run3Page`，不要依赖显示文本反查页面。
- 使用适合执行/同步语义的 Fluent 图标；三个 Run 可以共用同一图标，差异由文字和 badge 表达。
- 默认启动页面为 `Run 1`。
- 不提供新增、删除、重命名或动态刷新 Run 导航项的 API。
- 继续保留窗口底部 `StatusBar`，不改变状态栏消息机制。

## 7. 建议实施步骤

1. 将当前三个 `ComboWLoopContainer` 从 `WLoopPage` 的 `QTabWidget` 中移出，改为三个独立 Run 页面，每个页面只持有一个容器。
2. 删除 `WLoopPage` 对 `TabWidget`、`_run_containers` 聚合列表和 `running_count_changed` 的依赖；如果页面不再有调用方，则删除该旧页面文件或将其改造成单 Run 页面，二者只能保留一种实现。
3. 在 `MainWindow._setup_pages()` 中按固定顺序注册三个 Run 页面，并默认切换到 Run 1。
4. 在 `MainWindow` 中为三个 Run 分别连接 `run_state_changed(bool)`，实现逐项 badge 的显示和隐藏。
5. 清理旧的 WLoop 总数 badge 字段、总数回调和页面级聚合信号，避免遗留两套状态模型。
6. 只进行静态检查和人工 UI 验收，不执行 Python、pip、构建或虚拟环境相关命令。

## 8. 验收标准

- 启动后左侧只显示三个导航项：`Run 1`、`Run 2`、`Run 3`。
- 界面右侧不再出现 `QTabWidget` 或 `Run 1/2/3` 页面内 Tab。
- 三个 Run 页面均有独立的工作目录、Episode 控件、主 Play 按钮和状态历史。
- 在任意 Run 执行主 Play 时，仅对应导航项显示 badge `1`。
- 多个 Run 同时执行时，各自 badge 独立显示，不显示聚合总数。
- 任意 Run 完成后，其 badge 隐藏；其他仍运行的 Run badge 不受影响。
- 点击 Solo 不显示、隐藏或修改任何 Run badge。
- 切换导航页面不会中断其他 Run 的执行，也不会重置其界面状态。
- 固定只有三个 Run，不存在动态 Tab、动态导航项或新增/删除入口。
- `wwm` 不在本次修改范围内；`packages/combos`、`packages/coders` 不在本次修改范围内。

## 9. 风险与边界

### 页面生命周期风险

如果把容器直接临时创建在导航注册逻辑中，后续可能因页面销毁或重复初始化导致 worker 和状态丢失。因此三个 Run 页面和容器必须在窗口初始化期间创建一次，并由窗口或页面持有引用。

### badge 挂载时机风险

`InfoBadge` 依赖已经注册的导航 widget。必须先完成 `addSubInterface`，再建立 badge 更新逻辑；更新回调中也应处理 widget 不存在的保护分支。

### 并发执行边界

三个 Run 可以继续按现有逻辑并发执行。不同 Run 使用相同工作目录时的任务竞争、文件锁和任务领取语义不在本次 UI 重构范围内。

### 状态统计边界

本次不再统计运行中 Run 的总数。badge 只由对应容器的主 Run 状态驱动，Solo episode 的 worker 状态不纳入页面级状态。

## 10. 不在本次范围

- 不修改 `packages/combos` 中的 WLoop 状态机。
- 不修改 `packages/coders` 的执行能力。
- 不改造 `wwm` 的导航或 badge。
- 不增加动态 Run 管理能力。
- 不监听或汇总 Solo 执行状态。
- 不新增配置持久化、任务锁或跨 Run 调度机制。
