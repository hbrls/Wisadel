# WLoop UI 对齐 ALoop 重构方案

> updated_by: Codex - GPT-5
> updated_at: 2026-06-09 12:03:01

## 背景

当前需求以 `ALoop` 为设计基准，调整 `WLoop` 的 UI 层实现，使 `WLoop` 追上 `ALoop` 的页面结构、容器调用方式和新版 Selector 使用方式。

本方案只描述 UI 层改造，不修改 `packages/combos` 下的 domain 状态机。

## 约束

- 不修改 `packages/combos/wloop.py`。
- 不修改 `packages/combos/aloop.py`。
- 不提前抽公共组件、公共基类或共享抽象。
- 不处理 `packages/dashboard`。
- 先按 `ALoop` 现有实现方式，把 `WLoop` 一比一做一遍；完成后再在 review 环节判断是否存在值得复用的部分。

## 当前差异

### ALoop 当前形态

- `ALoopPage` 使用 `TabWidget` 创建 3 个 `ComboALoopContainer`。
- 每个 `ComboALoopContainer` 独立持有一个 `ALoop()` 实例。
- `ComboALoopContainer` 通过 `run_state_changed(bool)` 向页面汇报运行状态。
- `ALoopPage` 聚合 3 个 container 的运行状态，并通过 `running_count_changed(int)` 向 `MainWindow` 汇报运行数量。
- `ALoopSoloEpisode` 在构造阶段接收 `episode_id`、`prompt`、`is_dir`，并根据 `is_dir` 选择 `FileSelector` 或 `DirectorySelector`。

### WLoop 当前形态

- `WLoopPage` 只有一个 `ComboWLoopContainer`。
- `MainWindow` 直接访问 `wloop_page.wloop_container`，并监听单实例的 `play_started` / `play_stopped`。
- `WLoopSoloEpisode` 固定使用 `FileSelector`。
- `WLoopSoloEpisode` 通过后续 `set_prompt()`、`set_file_value()`、`set_working_directory()` 同步运行参数。
- `ComboWLoopContainer` 使用 `play_started` / `play_stopped` 汇报状态，不具备页面级运行数量聚合。
- `WLoop.__init__()` 使用 `self.EPISODES.copy()`，只浅拷贝列表；当前 `ComboWLoopContainer` 会修改 `episode.filename`，因此多个 `WLoop()` 实例如果直接并排使用，会共享同一个 `Episode` 对象并导致 tab 间文件选择互相污染。

## 目标设计

`WLoop` UI 改造成和 `ALoop` 同样的运行结构：

```text
WLoopPage
  └─ TabWidget
      ├─ Run 1: ComboWLoopContainer(run_id="run-1")
      ├─ Run 2: ComboWLoopContainer(run_id="run-2")
      └─ Run 3: ComboWLoopContainer(run_id="run-3")
```

每个 `ComboWLoopContainer`：

- 独立持有一个 `WLoop()` domain 实例。
- 在 UI 层为 `self.wloop.episodes` 创建独立的 `Episode` 对象副本，避免 domain 默认浅拷贝造成跨 tab 共享状态。
- 独立持有自己的工作目录选择器、episode UI、状态历史和运行按钮。
- 向 `WLoopPage` 发出 `run_state_changed(bool)`。

`WLoopPage`：

- 聚合 3 个 container 的运行状态。
- 对外发出 `running_count_changed(int)`。

`MainWindow`：

- 像处理 `ALoop` 一样处理 `WLoop` badge。
- 不再假设 `WLoopPage` 只有一个 `wloop_container`。

## 改造步骤

### Step 1：调整 WLoopPage 页面结构

参考 `ALoopPage` 的实现方式：

- 引入 `TabWidget`。
- 新增 `_run_containers` 列表。
- 创建 3 个 `ComboWLoopContainer(run_id=f"run-{i}")`。
- 每个 container 加入一个 tab，标题为 `Run 1`、`Run 2`、`Run 3`。
- 页面提供 `running_count_changed = Signal(int)`。
- 页面监听每个 container 的 `run_state_changed(bool)`，重新统计当前运行中的 container 数量。

### Step 2：调整 ComboWLoopContainer 的状态信号

参考 `ComboALoopContainer` 的信号形态：

- 将单实例语义的 `play_started` / `play_stopped` 调整为 `run_state_changed(bool)`。
- `ComboWLoopContainer.__init__()` 接收 `run_id: str = ""`，保存到 `self.run_id`。
- 创建 `WLoop()` 后，立即复制 `self.wloop.episodes` 中的每个 `Episode` 对象，保证每个 container 拥有独立 episode 配置。
- 开始执行 episode 时发出 `run_state_changed(True)`。
- 状态机进入 `FINISHED` 并 reset 后发出 `run_state_changed(False)`。
- 保留 container 内部 `_play_active`、`_state_history`、`_episode_map` 等现有运行结构。

episode 复制逻辑只放在 UI container 内，不修改 `packages/combos/wloop.py`：

```python
self.wloop = WLoop()
self.wloop.episodes = [
    Episode(id=ep.id, filename=ep.filename, prompt=ep.prompt, component=ep.component)
    for ep in self.wloop.episodes
]
```

### Step 3：调整 WLoopSoloEpisode 的构造与调用方式

参考 `ALoopSoloEpisode` 的新方式：

- 构造函数接收 `episode_id`、`prompt`、`is_dir`。
- 如果 `is_dir` 为 true，使用 `DirectorySelector`；否则使用 `FileSelector`。
- `set_working_directory()` 同步 selector 的 base directory。
- `set_file_value()` 同步 selector 展示值。
- `start_run()` 使用内部 `_prompt` 和 `_file_value` 生成 prompt。
- selector 的 `value_changed` 先同步内部 `_file_value`，再向外发出 `value_changed(str)`，避免内部展示值和实际运行值短暂不一致。

由于 `WLoop` 当前 episode 是 `.agents/workflows/w-execute/WORKFLOW.md`，默认仍会走 `FileSelector`。本步骤的重点不是新增目录选择能力，而是让调用方式和 `ALoopSoloEpisode` 对齐。

### Step 4：调整 ComboWLoopContainer 的 episode 创建方式

参考 `ComboALoopContainer` 的创建方式：

- 遍历 `self.wloop.episodes`。
- 对 `component == "WLoopSoloEpisode"` 的 episode，创建 `WLoopSoloEpisode(episode_id=ep.id, prompt=ep.prompt, is_dir=ep.filename.endswith("/"))`。
- 将 episode UI 放入 `_episodes` 和 `_episode_map`。
- `_sync_ui()` 负责把 working directory 和 filename 同步到 episode UI。
- `_on_file_changed()` 只更新当前 container 自己的 `self.wloop.episodes`，不能影响其他 tab。

### Step 5：调整 MainWindow 的 WLoop badge 逻辑

参考 `ALoop` 的 badge 聚合方式：

- `MainWindow` 监听 `self.wloop_page.running_count_changed`。
- 新增或调整 `_update_wloop_badge(count: int)`。
- count 为 0 时隐藏 badge。
- count 大于 0 时显示 count。
- 移除对 `wloop_page.wloop_container.play_started` 和 `play_stopped` 的单实例依赖。

## 验收点

- 人工验收：WLoop 页面显示 3 个 tab：`Run 1`、`Run 2`、`Run 3`。
- 人工验收：每个 tab 内都有独立的工作目录选择器、WLoop episode、运行按钮和状态历史。
- 人工验收：在 Run 1 修改文件选择后，Run 2 和 Run 3 的文件选择不被改变。
- 人工验收：每个 tab 通过主 Play 按钮独立运行，不影响其他 tab 的 UI 状态。
- 人工验收：任意 tab 通过主 Play 按钮运行时，主导航 WLoop badge 显示当前运行数量。
- 人工验收：所有 WLoop tab 停止后，主导航 WLoop badge 隐藏。
- `packages/combos/wloop.py` 没有变化。
- 没有新增公共抽象或共享基类。

## 风险与待确认

### 同一工作目录并发风险

3 个 WLoop tab 如果指向同一个 working directory，可能同时触发 `w-execute` 读取 `.context/TASK-*.md`。由于当前任务领取逻辑不在 UI 层做锁，同一任务存在被多个进程同时读取或处理的风险。

本次方案只追平 UI 结构，不解决任务队列并发语义。

### 状态统计风险

`running_count_changed(int)` 应以 container 的实际 `is_running()` 结果为准，而不是只依赖最近一次信号参数。这样可以避免信号丢失或状态边界导致 badge 数量错误。

### Solo 运行统计边界

本次对齐 `ALoop` 现有实现，只统计 container 主 Play 按钮触发的运行状态。单个 episode 的 `Solo` 按钮如果直接启动 worker，默认不驱动页面级 badge；如果产品期望 Solo 也计入运行数量，需要另起一轮同时改造 `ALoop` 和 `WLoop` 的 episode 级状态上报。

## 不在本次范围

- 不设计任务领取锁。
- 不调整 `w-execute` workflow。
- 不调整 `WLoop` domain 状态机。
- 不抽取 `ALoopSoloEpisode` / `WLoopSoloEpisode` 公共组件。
- 不统一 ALoop 和 WLoop 的 container 基类。
- 不把 Solo 按钮运行纳入主导航 badge 统计。
- 不处理 dashboard。
