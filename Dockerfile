FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-mcp.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-mcp.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/downloads /app/uploads /app/temp

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=capcut_server.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["python", "capcut_server.py"]