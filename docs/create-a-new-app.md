# 创建新应用文档

> updated_by: Cascade - Claude-Sonnet-4.5
> updated_at: 2026-04-10 18:55:00

本文档描述如何在 wishadel 项目中添加新的 desktop 应用包。

## 概述

wishadel 是一个多包 monorepo 项目，采用 packages 级别的模块架构。新应用应遵循本项目既定的目录结构、依赖规范和打包配置。

## 目录结构

```
wishadel/
├── docs/                          # 项目文档
├── packages/
│   ├── coders/                    # 代码生成/处理模块
│   ├── combos/                    # Combo 执行模块
│   └── wwm/                       # WWM (维维美) 桌面客户端
└── ...
```

### 新应用目录模板

推荐在 `packages/` 下创建独立应用目录：

```
packages/
└── your-app/
    ├── __init__.py
    ├── main.py                    # 应用入口
    ├── build.spec                 # PyInstaller 配置（如需打包）
    ├── build.bat                   # Windows 打包脚本（如需打包）
    ├── requirements.txt           # 依赖清单
    └── ui/                        # UI 模块（如需 UI）
        ├── __init__.py
        ├── main_window.py
        ├── styles.py
        ├── layout_window_title_bar.py  # 自定义标题栏组件
        ├── layout_window_status_bar.py # 状态栏组件
        └── layout_transparent.py       # 半透明面板组件
```

## 依赖管理

### requirements.txt 规范

```txt
# Internal packages (editable install)
-e ../combos

# External dependencies
PySide6>=6.6.0
PySide6-Addons>=6.6.0
PySide6-Essentials>=6.6.0
pyinstaller==6.11.1
```

### 内部包引用

- 使用 `-e ../package-name` 实现 editable install
- 确保 `pip install -e packages/your-app` 可正常执行
- 验证 `import your_package` 在安装后可用

### 安装命令

```bash
# 安装单个应用
pip install -e packages/your-app

# 安装所有依赖
pip install -r packages/your-app/requirements.txt
```

## 打包配置

### PyInstaller 配置 (build.spec)

```python
import os

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[],
    hiddenimports=[],
    ...
)
```

**关键配置说明：**

| 参数 | 说明 |
|------|------|
| `pathex` | 设为 `os.path.abspath('.')`，确保在包目录下执行 |
| `datas` | 如需包含资源文件，使用 `('src', 'dest')` 格式 |
| `hiddenimports` | 仅当动态导入时需要添加 |

### Windows 打包脚本 (build.bat)

```bat
@echo off
cd /d %~dp0
pyinstaller build.spec
pause
```

**关键点：**

- 使用 `cd /d %~dp0` 确保在 spec 文件所在目录执行
- 输出目录为 `dist/`

## UI 组件规范

### 命名约定

- UI 组件文件统一以 `layout_` 为前缀，例如 `layout_window_title_bar.py`
- 类名使用 PascalCase，与文件名对应，例如 `LayoutWindowTitleBar`
- `main_window.py` 只负责组装，不内联定义组件类

### 显式导入原则

- `__init__.py` 不做 re-export，不写 `from .xxx import Xxx`
- 所有使用方必须写完整路径：`from ui.layout_window_title_bar import LayoutWindowTitleBar`

### 透明窗口方案

无边框透明窗口使用 `FramelessWindowHint` + `WA_TranslucentBackground` 方案：

```python
self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
self.setAttribute(Qt.WA_TranslucentBackground)
```

- 自定义标题栏（`LayoutWindowTitleBar`）负责拖动和窗口控制按钮
- 半透明区域通过 `LayoutTransparent` 的 `paintEvent` 自绘实现，`alpha` 参数控制透明度
- 子组件需设置 `background: transparent` 和 `setAutoFillBackground(False)` 避免遮盖透明效果

## 设计决策记录

### UI 框架选择

- **选择**：PySide6
- **理由**：采用成熟的 Qt for Python 方案，GPL/LGPL 商业可用

### Shell 调用方式

- **选择**：由 packages/coders 提供 Shell 能力
- **理由**：统一 Shell 调用逻辑，避免重复实现

### 配置持久化

- **决策**：不实现配置持久化
- **理由**：用户每次手动选择工作目录，简化 v1 实现

## 验证清单

创建新应用后，请验证以下内容：

- [ ] `packages/your-app/` 目录结构完整
- [ ] `main.py` 可正常 import
- [ ] `requirements.txt` 包含所有依赖
- [ ] `pip install -r requirements.txt` 可正常执行
- [ ] `import your_package` 在安装后可用
- [ ] `build.spec` 语法正确
- [ ] `pyinstaller build.spec` 可正常执行
- [ ] `build.bat` 可正常执行
- [ ] 生成的 exe 可独立运行（如适用）
