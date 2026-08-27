# 开发规范

详细开发规范见：

- [桌面应用开发规范](docs/create-a-new-app.md)
- [活跃子项目模块规范](docs/create-a-new-module.md)

## 活跃项目

### 活跃应用

- `packages/wwm`
- `packages/w-execute`

开发、修改和验证工作默认围绕与任务直接相关的活跃应用进行。

### 活跃子项目

两个活跃应用均依赖以下子项目：

- `packages/coders`
- `packages/combos`

涉及活跃应用的功能开发时，可以根据依赖关系读取和修改这两个子项目。

## Python 环境与依赖安全

当前项目的 Python 虚拟环境由 PyCharm 手工管理，Agent 禁止接触虚拟环境和依赖安装相关部分。

- 禁止安装、升级、降级、卸载或以其他方式变更任何依赖。
- 禁止执行 `pip`、`python -m pip`、`uv`、`poetry`、`conda`、`virtualenv` 等依赖或环境管理命令。
- 禁止读取、修改、删除或执行任何 `.venv`、`venv` 等虚拟环境目录中的文件，包括其中的 Python、PyInstaller 和其他工具。
- 禁止使用系统级 Python、pip 或其他系统级包管理工具作为替代方案。
- 涉及 Python 运行、测试、构建或依赖验证时，Agent 只能进行静态检查，并明确说明相关命令未执行；实际操作由用户在 PyCharm 管理的环境中完成。

违反上述约束可能污染或损坏系统级 Python 环境，因此不得以验证、构建、排查或便利为理由绕过。

## 历史目录

以下目录属于历史问题，禁止读取、修改或重构：

- `packages/agents`
- `packages/dashboard`
- `packages/rime-ext`
- `packages/windows-app`

除非用户明确指定目录和任务，否则不要处理上述目录中的内容。
