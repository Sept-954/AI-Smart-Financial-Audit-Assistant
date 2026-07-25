"""PDF 文本分片——参考 Dexter chunker.ts 设计。"""

import hashlib


def estimate_tokens(text: str) -> int:
    """参考 Dexter estimateChunkTokens()。"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)


def merge_into_paragraphs(text_blocks: list[dict]) -> list[dict]:
    """将文本块按连续段落合并。参考 Dexter splitIntoParagraphs()。"""
    paragraphs = []
    current = ""
    start_page = 1
    end_page = 1
    current_type = ""
    
    for block in text_blocks:
        text = block.get("text", "").strip()
        if not text:
            continue
        if current:
            current += "\n\n" + text
        else:
            current = text
            start_page = block.get("page", 1)
            current_type = block.get("type", "")
        end_page = block.get("page", 1)
        
        # 遇到空行或段落结束标记时截断
        if text.endswith((".", "。", "!", "！", "?", "？")):
            paragraphs.append({
                "text": current,
                "start_page": start_page,
                "end_page": end_page,
                "type": current_type,
            })
            current = ""
    
    if current:
        paragraphs.append({
            "text": current,
            "start_page": start_page,
            "end_page": end_page,
            "type": current_type,
        })
    
    return paragraphs


def chunk_document(
    text_blocks: list[dict],
    chunk_tokens: int = 500,
    overlap_tokens: int = 100,
) -> list[dict]:
    """将文档分片。参考 Dexter chunkMemoryText()。"""
    paragraphs = merge_into_paragraphs(text_blocks)
    if not paragraphs:
        return []
    
    chunk_budget = int(chunk_tokens * 4)  # 粗略字符预算
    overlap_budget = int(overlap_tokens * 4)
    doc_id = hashlib.sha256(str(text_blocks[:100]).encode()).hexdigest()[:8]
    chunks = []
    i = 0
    
    while i < len(paragraphs):
        content = ""
        start_page = paragraphs[i]["start_page"]
        end_page = paragraphs[i]["end_page"]
        para_types = set()
        
        while i < len(paragraphs):
            p = paragraphs[i]
            candidate = content + "\n\n" + p["text"] if content else p["text"]
            if len(candidate) > chunk_budget and content:
                break
            content = candidate
            end_page = p["end_page"]
            para_types.add(p.get("type", ""))
            i += 1
        
        if not content:
            break
        
        chunks.append({
            "content": content,
            "start_page": start_page,
            "end_page": end_page,
            "doc_id": doc_id,
            "contains_table": "Table" in para_types,
        })
        
        # overlap 回退
        overlap_chars = 0
        j = i - 1
        while j >= 0 and overlap_chars < overlap_budget:
            overlap_chars += len(paragraphs[j]["text"])
            j -= 1
        i = max(i - 1, j + 1)
        if i >= len(paragraphs):
            break
    
    return chunks
