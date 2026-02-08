ARG PYTHON_IMAGE=3.12.9-slim
FROM python:${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 安装系统依赖（MySQL 客户端编译依赖）并安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config gcc \
    && python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 默认工作目录下运行 Gunicorn，监听 8000
EXPOSE 8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "module.survey_app.wsgi:application"]
