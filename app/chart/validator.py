import logging
logger = logging.getLogger(__name__)
def validate_chart_data(chart_data: dict, source_chunks: list[str]) -> dict:
    issues = []
    for point in chart_data.get("data", []):
        keys = list(point.keys())
        label = str(point.get(keys[0], "")) if keys else ""
        for key, val in point.items():
            if key == keys[0]:
                continue
            found = any(str(val) in chunk for chunk in source_chunks)
            if not found and isinstance(val, (int, float)):
                issues.append(f"{label} 的 {key}={val} 未在原文中找到匹配")
    if issues:
        chart_data["warning"] = "以下图表数据可能存在偏差，建议对照原文后再使用"
        chart_data["issues"] = issues[:5]
    return chart_data
