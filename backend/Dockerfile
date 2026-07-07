FROM mirror.ccs.tencentyun.com/library/python:3.11-slim

WORKDIR /app

# 腾讯云 apt 镜像
RUN sed -i 's|deb.debian.org|mirrors.tencent.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 腾讯云 PyPI 镜像
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.tencent.com/pypi/simple/ \
    --trusted-host mirrors.tencent.com

COPY . .

RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
