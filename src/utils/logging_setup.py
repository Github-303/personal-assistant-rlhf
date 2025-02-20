"""
Cấu hình logging cho hệ thống.
Cung cấp các tiện ích thiết lập và tùy chỉnh logging.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
import colorlog

def setup_logging(log_level: str = "INFO", 
                log_file: Optional[str] = None,
                config: Optional[Dict[str, Any]] = None) -> None:
    """
    Thiết lập cấu hình logging cho hệ thống.
    
    Args:
        log_level: Mức độ log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Đường dẫn file log (nếu không cung cấp, chỉ log ra console)
        config: Cấu hình hệ thống (tùy chọn)
    """
    # Đảm bảo thư mục log tồn tại nếu có file log
    if log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    # Chuyển đổi chuỗi log level thành hằng số
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Định dạng log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Định dạng màu cho console
    console_format = '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Tạo handler
    handlers = []
    
    # Console handler với màu
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        console_format,
        datefmt=date_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    handlers.append(console_handler)
    
    # File handler nếu có đường dẫn file
    if log_file:
        max_size = 5 * 1024 * 1024  # 5MB
        backup_count = 3
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        handlers.append(file_handler)
    
    # Cấu hình logging
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Thiết lập logging cho các thư viện bên thứ ba
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Ghi log khởi động
    logger = logging.getLogger("setup")
    logger.info(f"Đã khởi tạo logging với mức {log_level}" + 
               (f", đầu ra tới {log_file}" if log_file else ""))
    
    if config:
        logger.debug(f"Phiên bản hệ thống: {config.get('system', {}).get('version', 'unknown')}")

def get_logger(name: str) -> logging.Logger:
    """
    Lấy logger với tên chỉ định.
    
    Args:
        name: Tên của logger
        
    Returns:
        Đối tượng Logger
    """
    return logging.getLogger(name)
