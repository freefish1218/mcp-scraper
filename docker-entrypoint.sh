#!/bin/bash
# Docker容器启动脚本
# 配置Docker环境中的基础设置

set -e

# 检测是否在Docker环境中
if [ -f /.dockerenv ] || [ "$RUNNING_IN_DOCKER" = "true" ]; then
    echo "检测到Docker环境，配置基础环境..."
    
    # 设置Docker环境标识，让Python代码可以检测
    export RUNNING_IN_DOCKER=true
    export DOCKER_CONTAINER=true
    
    # 设置Playwright环境变量
    export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
    
    # 确保Chrome用户数据目录存在且有正确权限
    mkdir -p /tmp/chrome-user-data
    chown -R appuser:appuser /tmp/chrome-user-data
    
    echo "Docker环境配置完成，Chrome沙盒参数将由Python代码动态配置"
fi

# 启动应用
echo "启动MCP Scraper服务器..."
exec "$@"
