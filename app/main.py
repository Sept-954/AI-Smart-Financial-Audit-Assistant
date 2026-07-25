"""AI 财报智审助手 - FastAPI 入口。"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import upload_router, chat_router, settings_router, export_router

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。参考 OpenBB rest_api.py 的 lifespan 模式。"""
    logger.info("AI 财报智审助手启动")
    # 确保必要目录存在
    os.makedirs("./chroma_data", exist_ok=True)
    os.makedirs("./uploads", exist_ok=True)
    yield
    logger.info("AI 财报智审助手关闭")


app = FastAPI(
    title="AI 财报智审助手",
    description="上传财报 PDF，AI 自动分析并回答问题、生成图表、导出报告。零服务端存储，用户自带 API Key。",
    version="0.1.0",
    lifespan=lifespan,
)

# 挂载静态文件
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 注册路由 —— 参考 OpenBB 的路由组织方式
app.include_router(upload_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(export_router, prefix="/api")


@app.get("/")
async def home():
    """首页。返回 Jinja2 渲染的 HTML。"""
    from fastapi.responses import HTMLResponse
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("index.html")
    return HTMLResponse(content=template.render())


@app.get("/chat/{doc_hash}")
async def chat_page(doc_hash: str):
    """聊天页。"""
    from fastapi.responses import HTMLResponse
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("chat.html")
    return HTMLResponse(content=template.render(doc_hash=doc_hash))


@app.get("/settings")
async def settings_page():
    """设置页。"""
    from fastapi.responses import HTMLResponse
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("settings.html")
    return HTMLResponse(content=template.render())


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
