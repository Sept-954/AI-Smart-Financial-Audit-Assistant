"""多提供商 LLM 客户端——参考 Dexter llm.ts 设计。"""

import logging
from typing import Optional
from openai import OpenAI
from .providers import PROVIDER_CONFIG, resolve_provider

logger = logging.getLogger(__name__)


class LLMClient:
    """支持多提供商的 LLM 客户端。
    
    参考 Dexter src/model/llm.ts：
    - 前缀路由（providers.ts 风格）
    - 统一 OpenAI 兼容接口
    - 错误分类映射
    """
    
    def __init__(self, provider: str = "openai", api_key: str = "", model: str = ""):
        self.provider_id = provider
        config = resolve_provider(provider)
        if not config:
            raise ValueError(f"不支持的提供商: {provider}")
        
        self.model = model or config.default_model
        
        # Ollama 不需要 API Key
        if provider == "ollama":
            self.client = OpenAI(
                base_url=config.base_url or "http://127.0.0.1:11434/v1",
                api_key="ollama",
            )
        else:
            if not api_key:
                raise ValueError(f"{config.display_name} 需要 API Key")
            self.client = OpenAI(
                api_key=api_key,
                base_url=config.base_url,
            )
    
    def chat(self, messages: list[dict], stream: bool = False) -> dict:
        """发送聊天请求。返回 {'content': str, 'error': str | None}。"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
            )
            return {
                "content": response.choices[0].message.content or "",
                "error": None,
            }
        except Exception as e:
            error_info = self._classify_error(e)
            return {"content": "", "error": error_info}
    
    def chat_stream(self, messages: list[dict]):
        """流式聊天请求，返回 generator。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def test_connection(self) -> tuple[bool, str]:
        """测试 API 连通性。参考 PRD US-07：设置页连通性测试。"""
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                stream=False,
            )
            return True, "连接成功"
        except Exception as e:
            return False, self._classify_error(e)
    
    def _classify_error(self, error: Exception) -> str:
        """错误分类映射——参考 PRD 3.1 错误码映射表。"""
        msg = str(error)
        
        if "401" in msg or "Unauthorized" in msg or "invalid" in msg.lower() and "key" in msg.lower():
            return "API Key 无效或已过期，请前往设置页检查并更新 Key。"
        if "429" in msg or "Rate limit" in msg or "Too Many Requests" in msg:
            return "API 调用次数已用尽，请稍后重试，或检查 API 额度。"
        if "timeout" in msg.lower() or "timed out" in msg.lower():
            return "LLM 服务暂时无响应，请稍后重试。若持续失败，请检查 API 配置。"
        if "context" in msg.lower() and ("length" in msg.lower() or "token" in msg.lower()):
            return "当前对话过长，AI 无法一次处理。已自动截断部分历史内容，你可继续提问。"
        
        logger.error(f"[LLM_ERROR] provider={self.provider_id} model={self.model} msg={msg[:200]}")
        return "AI 回复异常，错误已记录。请重试或联系开发者。"
