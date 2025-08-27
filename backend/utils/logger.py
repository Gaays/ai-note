#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具 - 配置和管理应用程序日志
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则使用默认路径
    
    Returns:
        配置好的日志记录器
    """
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file is None:
        # 使用默认日志文件路径
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        today = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f'app_{today}.log'
    
    try:
        # 创建日志文件目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用RotatingFileHandler，当文件大小超过10MB时轮转
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        # 如果文件处理器创建失败，只使用控制台输出
        logger.warning(f"无法创建文件日志处理器: {e}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取已配置的日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器
    """
    return logging.getLogger(name)

def set_log_level(logger_name: str, level: str):
    """设置日志级别
    
    Args:
        logger_name: 日志记录器名称
        level: 日志级别
    """
    logger = logging.getLogger(logger_name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 同时设置所有处理器的级别
    for handler in logger.handlers:
        handler.setLevel(log_level)

def configure_root_logger(level: str = 'INFO'):
    """配置根日志记录器
    
    Args:
        level: 日志级别
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def disable_external_loggers():
    """禁用外部库的详细日志"""
    # 禁用一些常见的外部库日志
    external_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'openai',
        'anthropic',
        'google.generativeai',
        'faster_whisper'
    ]
    
    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志记录器"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger

# 应用启动时的日志配置
def init_app_logging(debug: bool = False):
    """初始化应用程序日志配置
    
    Args:
        debug: 是否启用调试模式
    """
    level = 'DEBUG' if debug else 'INFO'
    
    # 配置根日志记录器
    configure_root_logger(level)
    
    # 禁用外部库的详细日志
    disable_external_loggers()
    
    # 创建应用主日志记录器
    app_logger = setup_logger('video_note_app', level)
    app_logger.info(f"日志系统初始化完成，级别: {level}")
    
    return app_logger