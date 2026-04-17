"""
Volcengine Provider for smolagents

实现 smolagents 的 Model 接口，封装 Volcengine API 调用
使用 Anthropic SDK 风格的接口，但调用 Volcengine 服务
"""

from agents.providers._anthropic_compatiable_provider import _AnthropicCompatiableProvider
from agents.providers._config import Config


class VolcengineProvider(_AnthropicCompatiableProvider):
    """
    Volcengine Provider
    
    继承自 _AnthropicCompatiableProvider 基类
    仅 apiKey 从 ~/.config/wisadel/config.json 的 providers.volcengine.options 下读取。
    baseUrl 与 model 由本类常量 BASE_URL / MODEL 维护，不走配置。
    """
    
    BASE_URL = "https://ark.cn-beijing.volces.com/api/compatible"
    MODEL = "glm-4-7-251222"
    
    def __init__(self):
        """
        初始化 Volcengine Provider
        
        通过 Config.get_provider("volcengine") 读取 apiKey。
        """
        config = Config()
        api_key = config.get_provider("volcengine")
        super().__init__(
            api_key=api_key,
            model=self.MODEL,
            base_url=self.BASE_URL,
        )
    
    @staticmethod
    def probe() -> None:
        """
        探测 Volcengine 模型的身份信息
        
        向模型发送一组身份探针问题，直接打印响应，无返回值。
        用于快速验证 config / 网络 / 模型接入是否正常。
        """
        prompt = (
            "- 你是谁？\n"
            "- 你由哪家公司开发？\n"
            "- 你的模型名称和版本是什么？\n"
            "- 你的知识截止日期是什么时候？"
        )
        provider = VolcengineProvider()
        response = provider([{"role": "user", "content": prompt}])
        print(response)
