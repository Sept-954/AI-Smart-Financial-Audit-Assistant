"""聊天问答路由——PRD 2.1 P0。"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.llm.client import LLMClient
from app.llm.prompts import SYSTEM_PROMPT, QA_PROMPT
from app.llm.context import ContextManager
from app.chart.generator import render_chart, parse_chart_json
from app.chart.validator import validate_chart_data
from app.vector.index import ChromaIndex

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

chroma_index = ChromaIndex()

# 全局上下文管理（session 级别，实际应绑定到会话 ID）
context_manager = ContextManager()


def build_context_chunks(documents: list[str], metadatas: list[dict]) -> str:
    """将检索结果组装为上下文文本。"""
    parts = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        page_info = f"【第{meta.get('start_page', '?')}页】" if meta else ""
        parts.append(f"[片段 {i+1}] {page_info}\n{doc[:1000]}")
    return "\n\n".join(parts)


@router.post("/chat")
async def chat(body: dict):
    """处理聊天问答请求。
    
    请求体：
    {
        "doc_hash": "abc12345",
        "question": "2023年营收是多少？",
        "provider": "openai",
        "api_key": "sk-xxx",
        "model": "gpt-4o"
    }
    """
    doc_hash = body.get("doc_hash", "")
    question = body.get("question", "")
    provider = body.get("provider", "openai")
    api_key = body.get("api_key", "")
    model = body.get("model", "")
    
    if not doc_hash or not question:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    
    if not api_key:
        return JSONResponse(content={
            "answer": "请先在设置中填入 API Key 后再提问。",
            "has_chart": False,
        })
    
    try:
        # 1. 检索相关上下文
        search_result = chroma_index.search(doc_hash, question)
        context = build_context_chunks(
            search_result.get("documents", []),
            search_result.get("metadatas", []),
        )
        
        # 2. 构造 LLM Prompt
        llm = LLMClient(provider=provider, api_key=api_key, model=model)
        history_summary = context_manager.get_history_summary()
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                current_date=datetime.now().strftime("%Y-%m-%d")
            )},
            {"role": "user", "content": QA_PROMPT.format(
                context_chunks=context,
                history_summary=history_summary,
                question=question,
            )},
        ]
        
        # 3. 调用 LLM
        result = llm.chat(messages)
        
        if result["error"]:
            return JSONResponse(content={"answer": result["error"], "has_chart": False})
        
        answer = result["content"]
        
        # 4. 记录对话到上下文管理器
        context_manager.add_turn(question, answer)
        
        # 5. 检查是否包含图表请求
        has_chart = False
        chart_html = None
        chart_data = parse_chart_json(answer)
        if chart_data:
            # 校验图表数据
            validated = validate_chart_data(chart_data, search_result.get("documents", []))
            warning = validated.get("warning", "")
            chart_html = render_chart(validated)
            has_chart = True
            if warning:
                answer += f"\n\n> ⚠️ {warning}"
        
        return JSONResponse(content={
            "answer": answer,
            "has_chart": has_chart,
            "chart_html": chart_html,
        })
    
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        return JSONResponse(content={"answer": f"处理失败: {str(e)}", "has_chart": False})
