ARG PYTHON_IMAGE=3.12.9-slim
FROM python:${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 先把容器内 apt 源切到腾讯云镜像，避免默认 Debian 源过慢
RUN sed -i \
    -e 's#http://deb.debian.org/debian#https://mirrors.cloud.tencent.com/debian#g' \
    -e 's#http://deb.debian.org/debian-security#https://mirrors.cloud.tencent.com/debian-security#g' \
    /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config gcc \
    && rm -rf /var/lib/apt/lists/*

# 单独安装 Python 依赖，命中缓存时只会重跑这一层
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -i https://mirrors.cloud.tencent.com/pypi/simple --no-cache-dir -r /app/requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 默认工作目录下运行 Gunicorn，监听 8000
EXPOSE 8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "module.survey_app.wsgi:application"]
