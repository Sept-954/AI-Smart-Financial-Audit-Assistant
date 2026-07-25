"""表格提取质量检测——PRD 3.3/4.1 表格提取质量检测阈值。"""

from bs4 import BeautifulSoup


def assess_table_quality(table_html: str) -> dict:
    """检测单张表格的提取质量。
    质量阈值（PRD 4.1）：
    - 提取行 < 3 行 -> 标记异常
    - 合并单元格比例 > 30% -> 标记异常
    """
    try:
        soup = BeautifulSoup(table_html, "lxml")
    except Exception:
        return {"status": "low", "reason": "HTML解析失败", "detail": {}}
    rows = soup.find_all("tr")
    if len(rows) < 3:
        return {"status": "low", "reason": f"提取行数过少({len(rows)}行)", "detail": {"rows": len(rows)}}
    merged = soup.find_all(["td", "th"], attrs={"colspan": True}) + \
             soup.find_all(["td", "th"], attrs={"rowspan": True})
    total = len(soup.find_all(["td", "th"]))
    merge_ratio = len(merged) / total if total > 0 else 0
    if merge_ratio > 0.3:
        return {"status": "low", "reason": f"合并单元格比例过高({merge_ratio:.0%})", "detail": {"merge_ratio": merge_ratio, "total_cells": total}}
    return {"status": "ok", "reason": "", "detail": {"rows": len(rows), "cells": total}}


def assess_document_tables(tables: list[str]) -> dict:
    """检测整份文档的表格提取质量。"""
    results = []
    low_count = 0
    for i, tbl in enumerate(tables):
        r = assess_table_quality(tbl)
        r["table_index"] = i
        results.append(r)
        if r["status"] == "low":
            low_count += 1
    overall = "ok"
    msg = ""
    if low_count > 0:
        overall = "low"
        ratio = low_count / max(len(tables), 1)
        msg = f"表格提取不完整（{low_count}/{len(tables)}张表格质量低于阈值）" if ratio >= 0.2 else f"部分表格可能不完整（{low_count}张）"
    return {"overall": overall, "total_tables": len(tables), "low_quality_count": low_count, "message": msg, "details": results}
