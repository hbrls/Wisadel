# Rime 扩展 MVP 实现计划

## 目标
基于 Rime + Lua 实现整段润色输入插件，支持：
* 整段文本暂存 → 整段润色 → 一次性上屏
* 为独立悬浮 GUI 提供标准数据/指令交互能力
* 用户可独立安装/卸载

## 技术约束
* 平台：Windows Rime（小狼毫）≥0.14.3
* 扩展语言：Lua 5.1（Rime 原生内置）
* 部署方式：文件放入 Rime 用户目录 + 重新部署
* 核心钩子：`init`、`processor_key_event`、`context_update`、`composer_commit`
* 交互方式：共享内存读取 + 系统快捷键模拟

## 实现步骤

### 阶段 1：最小原型（Very Small MVP） - ✅ 已完成
- **任务**：验证 Rime + Lua 集成可行
- **实现**：
  1. `wisadel.lua` - `M.init(env)` 初始化函数
  2. `wisadel.schema.yaml` - 基础 schema 配置
- **验证**：部署后日志输出 "wisadel.lua initialized"

### 阶段 2：处理器钩子 - ✅ 已完成
- **任务**：按键监听，不拦截
- **实现**：
  1. `M.key_processor(key, env)` - 打印按键码
  2. Schema 中启用 `lua_processor@key_processor`
- **验证**：任意输入框按键，日志输出按键码

### 阶段 3：核心机制实现（进行中）
- [ ] **3.1 上下文变量实现**
  - 实现 `para_mode` 状态变量
  - 实现 `para_buffer` 暂存区
  - 在 `init` 钩子中初始化变量
- [ ] **3.2 模式开关机制**
  - 在 `key_processor` 中识别快捷键（`Ctrl+Shift+P` 开启，`Ctrl+Shift+X` 关闭）
  - 实现整段模式开启时的原生上屏拦截
- [ ] **3.3 文本暂存**
  - 在 `context_update` 中捕获选字结果并追加至 `para_buffer`
  - 同步处理原生删改操作

### 阶段 4：润色与提交
- [ ] **4.1 润色逻辑**
  - 实现基础润色规则（标点规范化、空格清理）
  - 确保润色处理 ≤100ms/200字
- [ ] **4.2 一次性上屏**
  - 在 `composer_commit` 中读取 `para_buffer` 执行润色
  - 将润色后文本赋值给 Rime 原生提交字段
  - 上屏后重置 `para_mode=false` + 清空 `para_buffer`

### 阶段 5：GUI 交互
- [ ] **5.1 数据暴露**
  - 确认 Context 变量同步至 Rime 原生共享内存
  - 验证 GUI 可读取 `para_mode` 和 `para_buffer`
- [ ] **5.2 快捷键触发**
  - GUI 通过模拟系统快捷键触发 Rime 扩展逻辑

### 阶段 6：验收与优化
- [ ] 功能验收：模式开关、整段暂存、原生能力保留、一次性上屏
- [ ] 性能验收：响应速度、润色速度、资源占用
- [ ] 兼容性验收：Rime 版本、系统版本、应用兼容、插件兼容

## 文件组成
| 文件 | 作用 |
|------|------|
| `wisadel.lua` | 核心 Lua 脚本（初始化、钩子、暂存、润色、状态管理） |
| `wisadel.schema.yaml` | Schema 配置（加载 Lua、声明快捷键、关联输入法） |

## 快捷键定义
| 功能 | 默认快捷键 |
|------|------------|
| 开启整段模式 | `Ctrl+Shift+P` |
| 关闭整段模式 | `Ctrl+Shift+X` |
| 整段润色上屏 | `Ctrl+Enter` |
| 清空暂存区 | `Ctrl+Backspace` |
