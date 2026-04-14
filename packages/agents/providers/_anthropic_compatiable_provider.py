"""
Anthropic Compatible Provider Base

抽取 Anthropic SDK 调用逻辑的公共基类
子类只需指定 BASE_URL 和默认 model 值
"""

from typing import List, Dict, Any, Optional
from smolagents.models import Model, ChatMessage, MessageRole
import anthropic
import anthropic.types


class _AnthropicCompatiableProvider(Model):
    """
    Anthropic 兼容 Provider 基类
    
    继承自 smolagents 的 Model 接口
    子类需要指定:
    - BASE_URL: API 端点地址
    - 默认 model 值
    """
    
    # 子类必须覆盖
    BASE_URL: str = ""
    
    def __init__(self, api_key: str, model: str):
        """
        初始化 Provider
        
        Args:
            api_key: API Key
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        self._client: Optional[anthropic.Anthropic] = None
    
    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy init client"""
        if self._client is None:
            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.BASE_URL
            )
        return self._client
    
    def _convert_messages(
        self, 
        messages: List[ChatMessage]
    ) -> tuple[Optional[str], List[anthropic.types.MessageParam]]:
        """
        将 ChatMessage 列表转换为 Anthropic API 格式
        
        Args:
            messages: smolagents ChatMessage 列表
            
        Returns:
            (system_message, anthropic_messages) 元组
        """
        system_message: Optional[str] = None
        anthropic_messages: List[anthropic.types.MessageParam] = []
        
        for msg in messages:
            if msg.role == MessageRole.ASSISTANT:
                # 处理 assistant 消息（包含 tool calls）
                anthropic_messages.append({
                    "role": "assistant",
                    "content": msg.content or ""
                })
            elif msg.role == MessageRole.USER:
                anthropic_messages.append({
                    "role": "user",
                    "content": msg.content or ""
                })
            elif msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": str(msg.role),
                    "content": msg.content or ""
                })
        
        return system_message, anthropic_messages
    
    def _extract_text_content(self, response) -> str:
        """
        从 API 响应中提取文本内容
        
        Args:
            response: Anthropic API 响应对象
            
        Returns:
            文本内容字符串
        """
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text
        return text_content
    
    def generate(
        self,
        messages: List[ChatMessage],
        stop_sequences: Optional[List[str]] = None,
        response_format: Optional[Dict[str, str]] = None,
        tools_to_call_from: Optional[List] = None,
        **kwargs
    ) -> ChatMessage:
        """
        调用 API，返回 ChatMessage
        
        Args:
            messages: 消息列表（smolagents ChatMessage 格式）
            stop_sequences: 停止序列
            response_format: 响应格式
            tools_to_call_from: 可用工具列表
            **kwargs: 其他参数
            
        Returns:
            ChatMessage
        """
        # 转换消息格式
        system_message, anthropic_messages = self._convert_messages(messages)
        
        # 构建 API 调用参数
        api_params: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": anthropic_messages
        }
        
        if system_message:
            api_params["system"] = system_message
        
        # 调用 API
        response = self.client.messages.create(**api_params)
        
        # 提取文本内容
        text_content = self._extract_text_content(response)
        
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=text_content,
            raw=response
        )
    
    def __call__(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        调用 API，返回完整响应文本
        
        Args:
            messages: 消息列表（dict 格式）
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            完整响应文本
        """
        try:
            # 转换为 ChatMessage 格式
            chat_messages = []
            for msg in messages:
                role = MessageRole(msg["role"]) if msg["role"] in ["user", "assistant", "system"] else MessageRole.USER
                chat_messages.append(ChatMessage(role=role, content=msg["content"]))
            
            response = self.generate(chat_messages, **kwargs)
            return response.content.strip()
            
        except anthropic.APIError as e:
            raise RuntimeError(f"API 调用失败: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"处理响应失败: {str(e)}") from e
