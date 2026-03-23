"""跨包导入代理模块 - 使用 importlib 显式加载 coders 模块

此模块提供跨包导入能力，允许 dashboard 模块访问 packages/coders 模块，
而无需修改 sys.path，确保模块隔离性。
"""

import importlib.util
import importlib
import os
import sys
from loguru import logger

# 计算 coders 模块路径（兼容开发环境 / PyInstaller 打包环境）
if getattr(sys, "frozen", False):
    _base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    _runtime_env = "pyinstaller"
else:
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _base_path = os.path.dirname(_current_dir)
    _runtime_env = "development"

_coders_module_path = os.path.join(_base_path, "coders", "__init__.py")

# 优先使用常规导入（适用于已被 PyInstaller 正确收集为模块的场景）
try:
    coders = importlib.import_module("coders")
except ImportError:
    # 回退到按文件路径加载（适用于作为数据文件分发的场景）
    _spec = importlib.util.spec_from_file_location("coders", _coders_module_path)
    if _spec is None or _spec.loader is None:
        raise ImportError(
            "无法加载 coders 模块："
            f"尝试路径={_coders_module_path}，"
            "请确认 Dashboard.spec 已包含 datas=[('../coders', 'coders')]"
        )

    coders = importlib.util.module_from_spec(_spec)

    # 设置 __package__ 属性以支持相对导入
    coders.__package__ = "coders"

    # 将模块添加到 sys.modules 以支持相对导入
    sys.modules["coders"] = coders

    # 执行模块代码
    _spec.loader.exec_module(coders)

logger.info(f"跨包导入 coders 模块成功（env={_runtime_env}）")

# 导出 coders 模块中的类和函数
KiloCode = coders.KiloCode
ClaudeCode = coders.ClaudeCode
run_command = coders.run_command
run_prompt = coders.run_prompt
probe = coders.probe

__all__ = ["coders", "KiloCode", "ClaudeCode", "run_command", "run_prompt", "probe"]
