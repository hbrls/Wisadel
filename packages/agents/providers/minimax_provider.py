"""
Minimax Provider for smolagents

实现 smolagents 的 Model 接口，封装 Minimax API 调用
使用 Anthropic SDK 风格的接口，但调用 Minimax 服务
"""

from typing import Optional
from agents.providers._anthropic_compatiable_provider import _AnthropicCompatiableProvider


class MinimaxProvider(_AnthropicCompatiableProvider):
    """
    Minimax Provider
    
    继承自 _AnthropicCompatiableProvider 基类
    仅保留 Minimax 专属的 BASE_URL 和默认 model 值
    """
    
    BASE_URL = "https://api.minimaxi.com/anthropic"
    DEFAULT_MODEL = "MiniMax-M2.7"
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        初始化 Minimax Provider
        
        Args:
            api_key: Minimax API Key
            model: 模型名称（默认 MiniMax-M2.1）
        """
        super().__init__(api_key=api_key, model=model or self.DEFAULT_MODEL)
