FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements-mcp.txt ./

# 安装Python依赖（使用国内镜像加速）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-mcp.txt

# 复制项目文件
COPY . .

# 创建配置文件
RUN cp config.json.example config.json

# 创建必要的目录
RUN mkdir -p drafts media logs

# 暴露端口
EXPOSE 9001

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "Starting CapCutAPI..."\n\
echo "Starting HTTP API server on port 9001..."\n\
python capcut_server.py &\n\
HTTP_PID=$!\n\
echo "HTTP API server started with PID: $HTTP_PID"\n\
\n\
echo "Starting MCP server..."\n\
python mcp_server.py &\n\
MCP_PID=$!\n\
echo "MCP server started with PID: $MCP_PID"\n\
\n\
# 捕获终止信号并优雅关闭\n\
trap "kill $HTTP_PID $MCP_PID" EXIT\n\
\n\
# 等待进程结束\n\
wait $HTTP_PID $MCP_PID' > /app/start.sh && \
    chmod +x /app/start.sh

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# 启动命令
CMD ["/app/start.sh"]