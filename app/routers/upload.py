"""PDF 上传路由——PRD 2.1 P0。"""

import logging
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.pdf.parser import parse_pdf, compute_file_hash, cleanup_temp
from app.pdf.chunker import chunk_document
from app.vector.index import ChromaIndex

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])
UPLOAD_DIR = Path("./uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# 全局 Chroma 索引（单例）
chroma_index = ChromaIndex()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 财报文件。"""
    # 校验文件类型
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")
    
    # 校验文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 50MB 限制")
    
    # 保存临时文件
    UPLOAD_DIR.mkdir(exist_ok=True)
    temp_path = UPLOAD_DIR / f"{uuid4().hex}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
    
    try:
        # 解析 PDF
        parse_result = parse_pdf(str(temp_path))
        
        if parse_result["status"] == "error":
            raise HTTPException(status_code=422, detail=parse_result.get("error", "PDF 解析失败"))
        
        doc_hash = parse_result["file_hash"]
        
        # 分片
        chunks = chunk_document(parse_result["text_blocks"])
        if not chunks:
            raise HTTPException(status_code=422, detail="PDF 解析后无可用的文本内容")
        
        # 索引到 Chroma
        collection_name = chroma_index.index_report(doc_hash, chunks)
        
        result = {
            "doc_hash": doc_hash,
            "filename": file.filename,
            "pages": parse_result["pages"],
            "chunks": len(chunks),
            "tables": len(parse_result["tables"]),
            "parse_time_ms": parse_result["parse_time_ms"],
            "degraded": parse_result["degraded"],
            "table_quality": parse_result.get("table_quality", {}),
            "message": "解析完成",
        }
        
        # 如果表格提取被降级，附加提示
        if parse_result["degraded"]:
            table_msg = parse_result.get("table_quality", {}).get("message", "")
            result["message"] = f"解析完成，但{table_msg}" if table_msg else "解析完成，但部分表格提取不完整，建议对照原文"
        
        logger.info(f"上传成功: {file.filename} ({parse_result['pages']}页, {len(chunks)}片段)")
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        # 释放临时文件（零服务端存储原则）
        cleanup_temp(str(temp_path))


@router.get("/documents")
async def list_documents():
    """列出已索引的文档列表。"""
    collections = chroma_index.list_collections()
    return JSONResponse(content={"documents": collections})


@router.delete("/documents/{doc_hash}")
async def delete_document(doc_hash: str):
    """删除指定文档的索引。"""
    ok = chroma_index.delete_collection(doc_hash)
    return JSONResponse(content={"success": ok})
