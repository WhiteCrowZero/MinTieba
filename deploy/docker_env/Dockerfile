FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# 1）APT：只用清华源 + IPv4 + 重试/超时 + 系统依赖
RUN echo 'Acquire::ForceIPv4 "true"; Acquire::Retries "3"; Acquire::http::Timeout "10";' \
        > /etc/apt/apt.conf.d/99tuning \
 && rm -f /etc/apt/sources.list.d/debian.sources \
 && echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian trixie main contrib non-free non-free-firmware\n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian trixie-updates main contrib non-free non-free-firmware\n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free non-free-firmware" \
        > /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        libmariadb-dev \
        curl \
 && rm -rf /var/lib/apt/lists/*


# 2）安装 uv（pip 走清华源）
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install --upgrade pip \
 && pip install -i ${UV_INDEX_URL} uv

# 3）用 uv 安装依赖（替代 pip，也走清华源）
COPY requirements.txt ./requirements.txt
RUN uv pip install --system -r requirements.txt --index-url ${UV_INDEX_URL}

# 4）复制项目代码
COPY . .

# 默认 settings，可被 docker-compose 覆盖
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

# 启动脚本
COPY deploy/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]
