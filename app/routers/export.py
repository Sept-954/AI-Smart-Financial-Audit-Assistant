"""报告下载路由——PRD 2.1 P0。"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.export.report import generate_report

logger = logging.getLogger(__name__)
router = APIRouter(tags=["export"])


@router.post("/export")
async def export_report(body: dict):
    """导出分析报告为 PDF。
    
    请求体：
    {
        "chat_history": [{"question": "...", "answer": "..."}, ...],
        "title": "AI 财报分析报告"
    }
    """
    chat_history = body.get("chat_history", [])
    title = body.get("title", "AI 财报分析报告")
    
    if not chat_history:
        raise HTTPException(status_code=400, detail="没有可导出的对话内容")
    
    try:
        output_path = generate_report(chat_history, title)
        filename = f"财报分析报告_{Path(output_path).name}"
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=filename,
        )
    except Exception as e:
        logger.error(f"报告导出失败: {e}")
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
