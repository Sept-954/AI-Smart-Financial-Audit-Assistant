"""PDF 解析管线——Unstructured + PyMuPDF 兜底。"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PDFParsingError(Exception):
    pass


def compute_file_hash(file_path: str) -> str:
    """计算文件 SHA256 哈希前 8 位，用于 Chroma collection 命名。"""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]


def parse_pdf(
    file_path: str,
    timeout: int = 60,
) -> dict:
    """解析 PDF 文件，返回文本块和表格。
    
    策略（PRD 3.3）：
    1. 先用 Unstructured partition_pdf（hi_res + 中文 + 表格提取）
    2. 如果表格提取质量低于阈值，标记"表格提取不完整"
    3. 如果解析失败/超时，降级到 PyMuPDF 纯文本提取
    """
    result = {
        "status": "ok",
        "pages": 0,
        "text_blocks": [],
        "tables": [],
        "table_quality": {},
        "degraded": False,
        "error": None,
        "parse_time_ms": 0,
        "file_hash": compute_file_hash(file_path),
    }
    
    start = time.time()
    
    # 策略 1：Unstructured 主解析
    try:
        _parse_with_unstructured(file_path, result, timeout)
    except Exception as e:
        logger.warning(f"Unstructured 解析失败，降级到 PyMuPDF: {e}")
        result["degraded"] = True
        # 策略 2：PyMuPDF 纯文本兜底
        try:
            _parse_with_pymupdf(file_path, result)
        except Exception as e2:
            result["status"] = "error"
            result["error"] = f"PDF 解析失败: {e2}"
    
    result["parse_time_ms"] = int((time.time() - start) * 1000)
    
    # 表格质量检测
    if result["tables"]:
        from app.pdf.quality import assess_document_tables
        result["table_quality"] = assess_document_tables(result["tables"])
        if result["table_quality"]["overall"] == "low":
            result["degraded"] = True
            logger.info(f"表格提取质量低: {result['table_quality']['message']}")
    
    return result


def _parse_with_unstructured(file_path: str, result: dict, timeout: int) -> None:
    """使用 Unstructured 解析 PDF。"""
    from unstructured.partition.pdf import partition_pdf
    
    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",
        languages=["chi_sim"],
        extract_tables=True,
    )
    
    text_blocks = []
    tables = []
    max_page = 0
    
    for el in elements:
        page = el.metadata.page_number or 1
        max_page = max(max_page, page)
        
        if el.category == "Table":
            html = el.metadata.text_as_html or ""
            tables.append(html)
            text_blocks.append({
                "text": el.text or "",
                "page": page,
                "type": "Table",
            })
        else:
            text_blocks.append({
                "text": el.text or "",
                "page": page,
                "type": el.category,
            })
    
    result["pages"] = max_page
    result["text_blocks"] = text_blocks
    result["tables"] = tables


def _parse_with_pymupdf(file_path: str, result: dict) -> None:
    """PyMuPDF 纯文本提取兜底。"""
    import fitz  # PyMuPDF
    
    doc = fitz.open(file_path)
    text_blocks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_blocks.append({
                "text": text.strip(),
                "page": page_num + 1,
                "type": "Text",
            })
    
    result["pages"] = len(doc)
    result["text_blocks"] = text_blocks
    result["tables"] = []
    doc.close()


def cleanup_temp(file_path: str) -> None:
    """解析完成后释放原始 PDF。遵循 PRD 零服务端存储原则。"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"已释放临时文件: {file_path}")
    except Exception as e:
        logger.warning(f"清理文件失败: {e}")
