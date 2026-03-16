#!/usr/bin/env python3
"""
AI/CV Weekly - 结构化日志模块
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """控制台友好格式"""
    
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m",
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        return f"{color}[{record.levelname}]{reset} {record.getMessage()}"


def setup_logger(name: str = "ai_cv_weekly", log_dir: Path = None, 
                 level: str = "INFO", max_bytes: int = 10485760, 
                 backup_count: int = 5) -> logging.Logger:
    """
    配置日志
    
    Args:
        name: 日志器名称
        log_dir: 日志目录
        level: 日志级别
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数
    
    Returns:
        logging.Logger: 配置好的日志器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 确保日志目录存在
    if log_dir is None:
        log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件 Handler（结构化 JSON）
    log_file = log_dir / "weekly.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredLogFormatter())
    logger.addHandler(file_handler)
    
    # 控制台 Handler（友好格式）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)
    
    # 错误日志单独文件
    error_file = log_dir / "weekly.error.log"
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=max_bytes // 2,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredLogFormatter())
    logger.addHandler(error_handler)
    
    logger.info("日志系统初始化完成", extra={
        "extra_data": {"log_file": str(log_file), "level": level}
    })
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """获取日志器"""
    if name:
        return logging.getLogger(f"ai_cv_weekly.{name}")
    return logging.getLogger("ai_cv_weekly")


# 快捷方法
def debug(msg: str, **kwargs):
    get_logger().debug(msg, extra={"extra_data": kwargs} if kwargs else None)

def info(msg: str, **kwargs):
    get_logger().info(msg, extra={"extra_data": kwargs} if kwargs else None)

def warning(msg: str, **kwargs):
    get_logger().warning(msg, extra={"extra_data": kwargs} if kwargs else None)

def error(msg: str, **kwargs):
    get_logger().error(msg, extra={"extra_data": kwargs} if kwargs else None)

def critical(msg: str, **kwargs):
    get_logger().critical(msg, extra={"extra_data": kwargs} if kwargs else None)


if __name__ == "__main__":
    # 测试
    logger = setup_logger(level="DEBUG")
    logger.debug("调试信息", extra={"extra_data": {"test": True}})
    logger.info("普通信息", extra={"extra_data": {"items": 5}})
    logger.warning("警告信息")
    logger.error("错误信息", extra={"extra_data": {"code": 500}})
    
    # 测试快捷方法
    info("快捷方法测试", source="github", count=10)
