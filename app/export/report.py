import logging
from datetime import datetime
logger = logging.getLogger(__name__)
def generate_report(chat_history: list[dict], report_title: str = "AI 财报分析报告") -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    max_rounds = 50
    truncated = len(chat_history) > max_rounds
    if truncated:
        chat_history = chat_history[-max_rounds:]
    parts = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>
body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; color: #1a1a2e; }}
h1 {{ font-size: 22px; font-weight: 600; border-bottom: 2px solid #2563eb; padding-bottom: 12px; }}
.meta {{ color: #64748b; font-size: 14px; margin-bottom: 30px; }}
.qa-block {{ margin-bottom: 24px; page-break-inside: avoid; }}
.question {{ background: #f1f5f9; padding: 12px 16px; border-radius: 6px; font-weight: 500; }}
.question::before {{ content: "Q: "; font-weight: 700; color: #2563eb; }}
.answer {{ padding: 12px 16px; line-height: 1.6; }}
.answer::before {{ content: "A: "; font-weight: 700; color: #059669; }}
.truncated-note {{ background: #fef3c7; padding: 10px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; font-size: 14px; }}
th {{ background: #f8fafc; font-weight: 600; }}
</style></head><body>
<h1>{report_title}</h1>
<div class="meta">生成时间: {now} | AI 财报智审助手</div>"""]
    if truncated:
        parts.append(f'<div class="truncated-note">注意：对话超过{max_rounds}轮，本报告仅包含最近{max_rounds}轮问答。</div>')
    for item in chat_history:
        parts.append('<div class="qa-block">')
        parts.append(f'<div class="question">{item.get("question", "")}</div>')
        parts.append(f'<div class="answer">{item.get("answer", "")}</div>')
        parts.append('</div>')
    parts.append("</body></html>")
    output_path = f"/tmp/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    from weasyprint import HTML
    HTML(string="\n".join(parts)).write_pdf(output_path)
    return output_path
