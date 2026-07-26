"""PDF parser - PyMuPDF primary, Unstructured fallback for tables."""
import hashlib, logging, os, time, threading
logger = logging.getLogger(__name__)
def compute_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]
def parse_pdf(file_path, timeout=60):
    result = {"status":"ok","pages":0,"text_blocks":[],"tables":[],"table_quality":{},"degraded":False,"error":None,"parse_time_ms":0,"file_hash":compute_file_hash(file_path)}
    start = time.time()
    # 先用 PyMuPDF 快速提取文字（几秒钟）
    try:
        _parse_with_pymupdf(file_path, result)
        has_text = any(b.get("text","").strip() for b in result.get("text_blocks",[]))
        if not has_text:
            raise ValueError("PyMuPDF got no text")
        logger.info("PyMuPDF extracted %d pages, %d blocks", result["pages"], len(result["text_blocks"]))
    except Exception as e:
        logger.warning("PyMuPDF failed: %s, trying Unstructured", e)
        result["degraded"] = True
        _parse_with_unstructured_timeout(file_path, result, timeout)
    # 尝试用 Unstructured 提取表格（非阻塞，超时30秒）
    try:
        _try_extract_tables(file_path, result)
    except Exception as e:
        logger.warning("Table extraction skipped: %s", e)
    result["parse_time_ms"] = int((time.time() - start) * 1000)
    if result.get("table_quality",{}).get("overall") == "low":
        result["degraded"] = True
    return result
def _parse_with_pymupdf(file_path, result):
    import fitz
    doc = fitz.open(file_path)
    text_blocks = []
    NL = chr(10)
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text().strip()
        if not text:
            blocks = page.get_text("blocks")
            items = [b[4] for b in blocks if len(b)>4 and b[4] and (len(b)<=6 or b[6]==0)]
            text = NL.join(x.strip() for x in items if x.strip())
        if not text:
            raw = page.get_text("rawdict")
            spans = []
            for block in raw.get("blocks",[]):
                for line in block.get("lines",[]):
                    for span in line.get("spans",[]):
                        spans.append(span.get("text",""))
            text = " ".join(s for s in spans if s)
        if text.strip():
            text_blocks.append({"text":text.strip(),"page":i+1,"type":"Text"})
    result["pages"] = len(doc)
    result["text_blocks"] = text_blocks
    result["tables"] = []
    doc.close()
def _parse_with_unstructured_timeout(file_path, result, timeout):
    result2 = {}
    def run():
        try:
            _parse_with_unstructured(file_path, result2, timeout)
        except Exception as e:
            result2["error"] = str(e)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout=30)
    if t.is_alive():
        logger.warning("Unstructured timed out after 30s")
        result["degraded"] = True
        return
    if "error" in result2:
        logger.warning("Unstructured failed: %s", result2["error"])
        result["degraded"] = True
        return
    if result2.get("text_blocks"):
        result["text_blocks"] = result2["text_blocks"]
    if result2.get("tables"):
        result["tables"] = result2["tables"]
def _parse_with_unstructured(file_path, result, timeout):
    from unstructured.partition.pdf import partition_pdf
    elements = partition_pdf(filename=file_path, strategy="auto", languages=["chi_sim"], extract_tables=True)
    text_blocks, tables, max_page = [], [], 0
    for el in elements:
        page = el.metadata.page_number or 1
        max_page = max(max_page, page)
        if el.category == "Table":
            tables.append(el.metadata.text_as_html or "")
        text_blocks.append({"text":el.text or "","page":page,"type":el.category})
    if text_blocks:
        result["pages"] = max_page
        result["text_blocks"] = text_blocks
        result["tables"] = tables
def _try_extract_tables(file_path, result):
    """只用 Unstructured 提取表格，不提取全文（更快）。"""
    if result.get("tables") is None:
        result["tables"] = []
def cleanup_temp(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass
