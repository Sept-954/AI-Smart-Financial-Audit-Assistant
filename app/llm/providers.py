"""LLM 提供商配置——参考 Dexter providers.ts 的设计。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProviderConfig:
    id: str
    display_name: str
    api_key_env: Optional[str] = None
    base_url: str = ""
    default_model: str = ""
    fast_model: str = ""
    context_window: int = 128_000


# 提供商注册表 —— 参考 Dexter providers.ts 的前缀路由思路
PROVIDER_CONFIG: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        id="openai",
        display_name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o",
        fast_model="gpt-4o-mini",
        context_window=128_000,
    ),
    "deepseek": ProviderConfig(
        id="deepseek",
        display_name="DeepSeek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
        context_window=1_000_000,
    ),
    "qwen": ProviderConfig(
        id="qwen",
        display_name="通义千问",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
        context_window=128_000,
    ),
    "ollama": ProviderConfig(
        id="ollama",
        display_name="Ollama（本地）",
        base_url="http://127.0.0.1:11434/v1",
        default_model="qwen2.5:7b",
        context_window=128_000,
    ),
}


def resolve_provider(provider_id: str) -> Optional[ProviderConfig]:
    """按 ID 查提供商配置，参考 Dexter resolveProvider()。"""
    return PROVIDER_CONFIG.get(provider_id)


def detect_provider_by_model(model_name: str) -> str:
    """前缀路由：模型名前缀 → 提供商 ID。参考 Dexter 前缀路由设计。"""
    prefix_map = {
        "gpt-": "openai",
        "o1": "openai",
        "o3": "openai",
        "deepseek-": "deepseek",
        "qwen": "qwen",
        "qwen2": "qwen",
    }
    for prefix, provider_id in prefix_map.items():
        if model_name.startswith(prefix):
            return provider_id
    # 默认走 OpenAI
    return "openai"
