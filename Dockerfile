# 使用多阶段构建优化镜像大小

# 第一阶段：构建阶段，仅安装依赖
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives /tmp/* /var/tmp/*

# 先复制并安装基础依赖
COPY requirements.txt ./
# 安装所有依赖
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 安装项目本身
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install .


# 第二阶段：运行时阶段，仅复制依赖
FROM python:3.11-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    # 解决Chrome沙盒问题的环境变量
    CHROME_BIN=/opt/google/chrome/chrome \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome \
    # Docker环境标识
    RUNNING_IN_DOCKER=true \
    # Playwright Chrome启动参数
    PLAYWRIGHT_CHROME_ARGS="--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-features=TranslateUI --disable-ipc-flooding-protection --disable-background-networking --disable-default-apps --disable-extensions --disable-sync --disable-translate --hide-scrollbars --mute-audio --no-first-run --disable-breakpad --disable-infobars --window-position=0,0 --ignore-certificate-errors --ignore-ssl-errors --ignore-certificate-errors-spki-list"

WORKDIR /app

# 安装运行时依赖（包括 Chrome 所需的系统库）
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ca-certificates \
    curl \
    # Chrome/Chromium 依赖
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    # 解决沙盒问题需要的额外包
    libxss1 \
    libgconf-2-4 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives /tmp/* /var/tmp/*

# 复制依赖到最终镜像
COPY --from=builder /install /usr/local

# 创建必要的目录
RUN mkdir -p /app/cache /app/logs

# 只复制必要代码
COPY src/ ./src/
COPY patches/ ./patches/
COPY run_server.py ./
COPY clear_cache.sh ./
COPY docker-entrypoint.sh ./

# 设置启动脚本权限
RUN chmod +x docker-entrypoint.sh clear_cache.sh

# 安装Playwright浏览器（仅Chrome）
RUN python -m playwright install chrome --with-deps \
    # 清理不必要的浏览器数据
    && find /ms-playwright -name "*.zip" -delete \
    && find /ms-playwright -name "*firefox*" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /ms-playwright -name "*webkit*" -type d -exec rm -rf {} + 2>/dev/null || true \
    # 清理缓存
    && rm -rf /root/.cache /tmp/* /var/tmp/*

# 创建非特权用户
RUN groupadd -g 1000 appuser && useradd -u 1000 -r -m -g appuser appuser \
    # 创建必要的目录
    && mkdir -p /app/logs /app/cache /tmp/chrome-user-data \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /ms-playwright \
    && chown -R appuser:appuser /tmp/chrome-user-data \
    # 为 browserforge 数据目录设置权限，允许用户下载模型文件
    && mkdir -p /usr/local/lib/python3.11/site-packages/browserforge/fingerprints/data \
    && mkdir -p /usr/local/lib/python3.11/site-packages/browserforge/headers/data \
    && chown -R appuser:appuser /usr/local/lib/python3.11/site-packages/browserforge \
    # 确保Chrome可执行文件有正确权限
    && chmod +x /opt/google/chrome/chrome 2>/dev/null || true
USER appuser

# 环境变量
ENV DOCKER_CONTAINER=true

# 设置启动脚本
ENTRYPOINT ["./docker-entrypoint.sh"]

# 健康检查（如果没有 /health 端点，可以改为检查进程）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "run_server.py" || exit 1

CMD ["python", "run_server.py"]
