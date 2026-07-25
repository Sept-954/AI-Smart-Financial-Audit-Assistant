# AI 财报智审助手

上传上市公司财报 PDF，AI 自动解析并回答财务问题、生成分析图表、导出报告。

**隐私优先、零服务端** — PDF 和 API Key 均不经过任何第三方服务器。

---

## 功能

- PDF 上传解析：拖拽或点击上传，自动提取文本和表格
- AI 问答：基于财报内容的 RAG 式问答，所有回答标注数据来源页码
- 图表生成：一句指令生成交互式 Plotly 图表
- BYOK 自带 Key：支持 OpenAI / DeepSeek / 通义千问 / Ollama
- 报告导出：将对话记录导出为排版好的 PDF
- 隐私安全：零服务端存储，数据仅存本地浏览器

---

## 快速开始

### 前置要求

- Python 3.10+
- 一个 LLM API Key（OpenAI / DeepSeek / 通义千问 任选其一）

### 安装与运行

```bash
git clone https://github.com/Sept-954/AI-Smart-Financial-Audit-Assistant.git
cd AI-Smart-Financial-Audit-Assistant
pip install -r requirements.txt
python app/main.py
```

浏览器打开 **http://localhost:8000**

### 使用流程

1. 打开页面后，先点击右上角 **设置**
2. 选择 LLM 提供商，填入 API Key，点击"测试连接"验证
3. 回到首页，上传一份财报 PDF
4. 解析完成后自动进入聊天页，开始提问

---

## 技术栈

| 层 | 选型 |
|---|---|
| 后端框架 | FastAPI |
| 前端 | Jinja2 + 纯 CSS |
| PDF 解析 | Unstructured + PyMuPDF 兜底 |
| 向量数据库 | Chroma |
| LLM 接口 | OpenAI 兼容协议（多提供商） |
| 图表 | Plotly |

---

## 免责声明

本项目仅用于**教育学习和信息分析**，不构成任何投资建议。

---

## 参考项目

- [Dexter](https://github.com/virattt/dexter) — AI 金融研究 Agent
- [OpenBB](https://github.com/OpenBB-finance/OpenBB) — 开源金融数据平台
- [PRD-v0.2.md](./PRD-v0.2.md) — 产品需求文档
