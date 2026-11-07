# Google Cloud Run 部署用镜像
# Cloud Run 会通过环境变量 PORT（默认 8080）告诉容器监听哪个端口
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 1 个进程 + 8 个线程：内存占用小，足够应付当前流量；--timeout 0 交给 Cloud Run 控制请求超时
CMD exec gunicorn --bind :${PORT:-8080} --workers 1 --threads 8 --timeout 0 app:app
