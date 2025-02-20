"""
Module thiết lập các chức năng CLI
"""

import os
import sys
import logging
from typing import Optional

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Thiết lập logging
    
    Args:
        log_level: Mức độ ghi log
        log_file: Đường dẫn đến file log (tùy chọn)
    """
    # Tạo thư mục logs nếu cần
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
    # Định dạng log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Cấu hình logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    logger = logging.getLogger('setup')
    logger.info(f"Đã khởi tạo logging với mức {logging.getLevelName(log_level)}")
    
    # Tắt các log không cần thiết từ thư viện bên thứ ba
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)