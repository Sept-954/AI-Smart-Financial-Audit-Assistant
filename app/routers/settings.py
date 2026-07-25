"""设置路由——API Key 管理、连通性测试、数据清除。PRD 2.1 P0。"""

import logging
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.llm.providers import PROVIDER_CONFIG
from app.llm.client import LLMClient
from app.vector.index import ChromaIndex

logger = logging.getLogger(__name__)
router = APIRouter(tags=["settings"])

chroma_index = ChromaIndex()


@router.get("/providers")
async def list_providers():
    """列出所有支持的 LLM 提供商。"""
    providers = []
    for pid, config in PROVIDER_CONFIG.items():
        providers.append({
            "id": pid,
            "display_name": config.display_name,
            "default_model": config.default_model,
            "needs_key": config.api_key_env is not None,
        })
    return JSONResponse(content={"providers": providers})


@router.post("/settings/test-connection")
async def test_connection(body: dict):
    """测试 API Key 连通性。
    
    请求体：{"provider": "openai", "api_key": "sk-xxx", "model": "gpt-4o"}
    PRD US-07：格式校验 + 连通性测试。
    """
    provider = body.get("provider", "openai")
    api_key = body.get("api_key", "")
    model = body.get("model", "")
    
    if not api_key and provider != "ollama":
        return JSONResponse(content={"success": False, "message": "请输入 API Key"})
    
    # 格式校验（PRD US-07）
    if api_key and provider == "openai" and not api_key.startswith("sk-"):
        return JSONResponse(content={"success": False, "message": "API Key 格式不正确，OpenAI Key 以 sk- 开头"})
    
    try:
        client = LLMClient(provider=provider, api_key=api_key, model=model)
        success, message = client.test_connection()
        return JSONResponse(content={"success": success, "message": message})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)})


@router.post("/settings/validate-key")
async def validate_key(body: dict):
    """前端调用：纯格式校验，不发送网络请求。"""
    provider = body.get("provider", "openai")
    api_key = body.get("api_key", "")
    
    rules = {
        "openai": {"prefix": "sk-", "min_len": 20},
        "deepseek": {"prefix": "sk-", "min_len": 20},
        "qwen": {"prefix": "sk-", "min_len": 16},
    }
    
    rule = rules.get(provider, {})
    if not api_key:
        return JSONResponse(content={"valid": False, "message": "Key 不能为空"})
    prefix = rule.get("prefix", "")
    if prefix and not api_key.startswith(prefix):
        return JSONResponse(content={"valid": False, "message": f"Key 应以 {prefix} 开头"})
    min_len = rule.get("min_len", 0)
    if min_len and len(api_key) < min_len:
        return JSONResponse(content={"valid": False, "message": f"Key 长度不足（最少 {min_len} 位）"})
    
    return JSONResponse(content={"valid": True, "message": "格式正确"})


@router.post("/clear-all")
async def clear_all_data():
    """清除所有数据。
    PRD 3.1 数据清除机制：
    1. 删除 Chroma 目录
    2. 清空 localStorage（前端执行）
    3. 清空 sessionStorage（前端执行）
    """
    result = chroma_index.clear_all()
    # 删除 chroma 目录
    try:
        chroma_dir = Path("./chroma_data")
        if chroma_dir.exists():
            shutil.rmtree(chroma_dir)
            result["directory_cleared"] = True
    except Exception as e:
        result["directory_error"] = str(e)
    
    return JSONResponse(content={
        "success": True,
        "message": "服务端数据已清除",
        "detail": result,
    })
