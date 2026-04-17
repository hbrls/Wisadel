"""
Config Module

提供统一的配置文件读取功能，支持跨平台配置管理。
配置文件位于 ~/.config/wisadel/config.json
"""

import json
from pathlib import Path
from typing import Optional


class Config:
    """
    配置管理类
    
    只负责读取 ~/.config/wisadel/config.json，不包含任何 provider-specific 的知识。
    跨平台支持：Windows (C:\\Users\\<name>\\.config\\wisadel)，macOS/Linux (~/.config/wisadel)
    
    config.json 结构约定::
    
        {
          "providers": {
            "<name>": {
              "options": {
                "apiKey": "<string>"
              }
            }
          }
        }
    
    具体示例::
    
        {
          "providers": {
            "minimax": {
              "options": {
                "apiKey": "sk-xxxxxxxx"
              }
            }
          }
        }
    
    字段说明：
    - providers: 顶层对象，键为 provider 名（小写短名，如 "minimax"）
    - providers.<name>.options: 该 provider 的配置选项
    - providers.<name>.options.apiKey: 必填，provider 的 API Key
    
    不在 config 内的字段：
    - baseUrl / model：由各 Provider 以类常量形式维护
      （如 MinimaxProvider.BASE_URL、MinimaxProvider.MODEL），不通过 config.json 配置。
    
    Attributes:
        config_path: 配置文件路径
    """
    
    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "wisadel"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置读取器
        
        Args:
            config_path: 可选的配置文件路径，默认使用 ~/.config/wisadel/config.json
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self._config: dict = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """读取并解析配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            self._config = {}
    
    def get_provider(self, name: str) -> Optional[str]:
        """
        获取指定 provider 的 API Key
        
        读取路径：providers.<name>.options.apiKey
        其它字段（baseUrl、model 等）不由 config 管理，由各 Provider 自行维护。
        
        用法::
        
            api_key = config.get_provider("minimax")
        
        Args:
            name: provider 名称，例如 "minimax"
        
        Returns:
            apiKey 字符串；任意层级缺失时返回 None
        """
        providers = self._config.get("providers")
        if not isinstance(providers, dict):
            return None
        
        provider = providers.get(name)
        if not isinstance(provider, dict):
            return None
        
        options = provider.get("options")
        if not isinstance(options, dict):
            return None
        
        return options.get("apiKey")
