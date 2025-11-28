"""
日志系统配置模块
配置应用日志记录，包括文件日志和控制台日志
"""

import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(app):
    """
    配置应用日志系统
    
    Args:
        app: Flask应用实例
    """
    # 创建logs目录
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 配置文件日志处理器
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    
    # 设置日志格式
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # 设置日志级别
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # 配置控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    # 设置应用日志级别
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application logging initialized')
    
    return app
