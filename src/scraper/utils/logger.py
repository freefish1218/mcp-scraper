"""
结构化日志系统
支持标准格式和 JSON 格式日志
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
# 日志默认目录
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"


class StructuredLogger:
    """
    结构化日志记录器，支持标准格式化和 JSON 格式的日志。
    """
    
    def __init__(self, name: str, level: int = logging.INFO, log_dir: Path = DEFAULT_LOG_DIR, json_format: bool = False):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            log_dir: 日志目录
            json_format: 是否使用 JSON 格式
        """
        self.name = name
        self.level = level
        self.json_format = json_format
        
        # 确保日志目录存在
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志文件名
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = log_dir / f"{name}_{current_date}.log"
        
        # 初始化日志记录器
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # 清除现有处理器
        if logger.handlers:
            logger.handlers.clear()

        # 阻止日志冒泡        
        logger.propagate = False

        # 创建文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(self.level)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        
        # 设置格式化器
        if self.json_format:
            formatter = self._get_json_formatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_json_formatter(self):
        """获取 JSON 格式化器"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "name": record.name,
                    "level": record.levelname,
                    "message": record.getMessage(),
                }
                
                # 添加额外属性
                if hasattr(record, "props"):
                    log_data.update(record.props)
                
                return json.dumps(log_data, ensure_ascii=False)
        
        return JsonFormatter()
    
    def _log_with_props(self, level: int, msg: str, props: Optional[Dict[str, Any]] = None):
        """使用附加属性记录日志"""
        if props:
            self.logger.log(level, msg, extra={"props": props})
        else:
            self.logger.log(level, msg)
    
    def debug(self, msg: str, props: Optional[Dict[str, Any]] = None):
        """记录调试级别日志"""
        self._log_with_props(logging.DEBUG, msg, props)
    
    def info(self, msg: str, props: Optional[Dict[str, Any]] = None):
        """记录信息级别日志"""
        self._log_with_props(logging.INFO, msg, props)
    
    def warning(self, msg: str, props: Optional[Dict[str, Any]] = None):
        """记录警告级别日志"""
        self._log_with_props(logging.WARNING, msg, props)
    
    def error(self, msg: str, props: Optional[Dict[str, Any]] = None):
        """记录错误级别日志"""
        self._log_with_props(logging.ERROR, msg, props)
    
    def critical(self, msg: str, props: Optional[Dict[str, Any]] = None):
        """记录严重错误级别日志"""
        self._log_with_props(logging.CRITICAL, msg, props)
    
    def exception(self, msg: str, props: Optional[Dict[str, Any]] = None):
        """记录异常信息"""
        if props is None:
            props = {}
        
        self.logger.exception(msg, extra={"props": props})


def get_logger(name: str, level: str = "INFO", json_format: bool = False):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        json_format: 是否使用 JSON 格式
        
    Returns:
        日志记录器实例
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    
    return StructuredLogger(name, log_level, json_format=json_format)
