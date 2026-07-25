import json
import logging
from uuid import uuid4
import pandas as pd
import plotly.express as px
import plotly.io as pio
logger = logging.getLogger(__name__)
CHART_TEMPLATE = {"layout": {"template": "plotly_white", "font": {"family": "system-ui, sans-serif"}, "margin": {"t": 40, "r": 20, "b": 60, "l": 60}}}
def parse_chart_json(text: str) -> dict | None:
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "chart_type" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None
def render_chart(chart_data: dict) -> str:
    df = pd.DataFrame(chart_data["data"])
    x_col, y_col = df.columns[0], df.columns[1]
    title = chart_data.get("title", "")
    ct = chart_data.get("chart_type", "bar")
    if ct == "bar":
        fig = px.bar(df, x=x_col, y=y_col, title=title, text=y_col)
    elif ct == "line":
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
    elif ct == "pie":
        fig = px.pie(df, names=x_col, values=y_col, title=title)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title)
    fig.update_layout(**CHART_TEMPLATE["layout"])
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    chart_id = f"chart_{uuid4().hex[:8]}"
    return pio.to_html(fig, include_plotlyjs="cdn", full_html=False, div_id=chart_id)
