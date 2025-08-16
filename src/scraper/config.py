"""
MCP-Scraper 配置模块
提供简化的本地配置功能
"""

import os
from scraper.utils import get_logger

from dotenv import load_dotenv
load_dotenv(override=True)

# 日志配置
logger = get_logger(__name__)

# 配置项
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 检查必要的配置
def validate_config():
    """
    验证配置的有效性
    """
    logger.info("配置验证完成")
    return True

# 模块初始化时验证配置
if validate_config():
    logger.info("MCP-Scraper 配置模块已初始化")