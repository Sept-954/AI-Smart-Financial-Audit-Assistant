# 部署指南

## 方案一：Render（推荐，免费）

[Render](https://render.com) 提供免费 Web 服务，每月 750 小时运行时间。

### 部署步骤

1. **Fork 或推送代码到 GitHub**

2. **注册 Render 账号**（GitHub 登录即可）
   - 访问 https://dashboard.render.com
   - 点击 "New +" → "Web Service"
   - 连接你的 GitHub 仓库

3. **配置服务**
   - Name: `ai-finreport`（或任意名称）
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free**

4. **添加环境变量**（Settings → Environment）
   - `PYTHON_VERSION`: `3.12.0`

5. **添加磁盘**（Settings → Disk）
   - Name: `chroma-data`
   - Mount Path: `/var/data`
   - Size: 1 GB

6. 点击 **Deploy**，等待 3-5 分钟即可访问

### 注意事项

- Free 套餐 15 分钟无请求会自动休眠，再次访问会唤醒（约 30 秒）
- 为避免休眠，可设置 [UptimeRobot](https://uptimerobot.com) 定时 ping
- Chroma 数据存储在持久化磁盘上，重启不会丢失

---

## 方案二：Railway（备选）

[Railway](https://railway.app) 每月有 $5 免费额度。

1. 在 GitHub 创建仓库并推送代码
2. 登录 Railway，点击 "New Project" → "Deploy from GitHub repo"
3. 选择仓库
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 添加环境变量 `PYTHON_VERSION=3.12.0`
6. 添加卷（Volume）挂载到 `/chroma_data`

---

## 方案三：Hugging Face Spaces

适合展示 AI 功能，免费 CPU 实例。

1. 在 https://huggingface.co/new-space 创建 Space
2. SDK 选 **Docker**
3. 上传代码或连接 GitHub
4. Space 自动构建运行

---

## 部署后的操作

1. 打开部署后的 URL
2. 点击右上角 **设置**
3. 选择 LLM 提供商（OpenAI / DeepSeek / 通义千问）
4. 填入你的 API Key
5. 点击 **测试连接** 验证
6. 回到首页上传 PDF 财报开始使用

---

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 启动服务
python app/main.py
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000
