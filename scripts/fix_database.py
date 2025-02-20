#!/usr/bin/env python
"""
Script sửa chữa cấu trúc database
"""

import os
import sys
import argparse
import sqlite3
import logging
import shutil
from datetime import datetime

# Thêm thư mục gốc vào đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Khởi tạo logger mặc định
logger = logging.getLogger("fix_database")

def setup_logging(log_level=logging.INFO):
    """Cấu hình logging"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler()]
    )
    return logger

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Sửa chữa cấu trúc database")
    parser.add_argument("--db", type=str, default="data/feedback.db",
                        help="Đường dẫn đến file cơ sở dữ liệu phản hồi")
    parser.add_argument("--backup", action="store_true",
                        help="Tạo bản sao lưu trước khi sửa chữa")
    parser.add_argument("--force", action="store_true",
                        help="Ghi đè nếu bảng đã tồn tại")
    parser.add_argument("--verbose", action="store_true",
                        help="Hiển thị chi tiết quá trình sửa chữa")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Mức độ ghi log")
    
    return parser.parse_args()

def fix_database_schema(db_path: str, force: bool = False, backup: bool = True) -> bool:
    """
    Sửa lỗi schema trong database feedback
    
    Args:
        db_path: Đường dẫn đến file database
        force: True để ghi đè nếu bảng đã tồn tại
        backup: True để tạo bản sao lưu trước khi sửa chữa
        
    Returns:
        True nếu sửa thành công, False nếu không
    """
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(db_path):
        logger.error(f"Database không tồn tại: {db_path}")
        return False
    
    # Sao lưu database nếu được yêu cầu
    if backup:
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Đã sao lưu database vào {backup_path}")
        except Exception as e:
            logger.error(f"Không thể sao lưu database: {e}")
            if not force:
                return False
    
    conn = None
    try:
        # Kết nối đến database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Kiểm tra cấu trúc cơ sở dữ liệu
        logger.info("Kiểm tra cấu trúc cơ sở dữ liệu...")
        
        # Kiểm tra bảng feedback
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
        feedback_exists = cursor.fetchone() is not None
        
        if feedback_exists:
            logger.info("Bảng feedback đã tồn tại, kiểm tra cấu trúc...")
            cursor.execute("PRAGMA table_info(feedback)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            if "conversation_id" not in columns:
                logger.warning("Cột conversation_id không tồn tại trong bảng feedback, tiến hành sửa chữa...")
                
                # Tạo bảng tạm với cấu trúc mới
                cursor.execute('''
                CREATE TABLE feedback_temp (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    responses TEXT NOT NULL,
                    selected_response TEXT NOT NULL,
                    feedback_score REAL,
                    feedback_text TEXT,
                    metadata TEXT
                )
                ''')
                
                # Sao chép dữ liệu
                try:
                    # Lấy tên của các cột hiện có
                    existing_columns = list(columns.keys())
                    column_str = ", ".join(existing_columns)
                    
                    # Sao chép dữ liệu và thêm giá trị mặc định cho conversation_id
                    cursor.execute(f"INSERT INTO feedback_temp ({column_str}, conversation_id) SELECT {column_str}, '' FROM feedback")
                    copy_count = cursor.rowcount
                    logger.info(f"Đã sao chép {copy_count} dòng dữ liệu từ bảng cũ")
                    
                    # Xóa bảng cũ
                    cursor.execute("DROP TABLE feedback")
                    
                    # Đổi tên bảng tạm thành feedback
                    cursor.execute("ALTER TABLE feedback_temp RENAME TO feedback")
                    
                    # Tạo lại các chỉ mục
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON feedback(conversation_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)')
                    
                    logger.info("Đã sửa chữa thành công bảng feedback")
                    
                except Exception as e:
                    logger.error(f"Lỗi khi sao chép dữ liệu: {e}")
                    conn.rollback()
                    return False
            else:
                logger.info("Cấu trúc bảng feedback đã đúng")
        else:
            logger.info("Bảng feedback không tồn tại, tạo mới...")
            cursor.execute('''
            CREATE TABLE feedback (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                query TEXT NOT NULL,
                responses TEXT NOT NULL,
                selected_response TEXT NOT NULL,
                feedback_score REAL,
                feedback_text TEXT,
                metadata TEXT
            )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON feedback(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)')
            logger.info("Đã tạo bảng feedback mới")
        
        # Kiểm tra bảng comparisons
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comparisons'")
        comparisons_exists = cursor.fetchone() is not None
        
        if not comparisons_exists:
            logger.info("Bảng comparisons không tồn tại, tạo mới...")
            cursor.execute('''
            CREATE TABLE comparisons (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                query TEXT NOT NULL,
                chosen TEXT NOT NULL,
                rejected TEXT NOT NULL,
                chosen_model TEXT NOT NULL,
                rejected_model TEXT NOT NULL,
                metadata TEXT
            )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparisons_conversation ON comparisons(conversation_id)')
            logger.info("Đã tạo bảng comparisons mới")
        else:
            logger.info("Bảng comparisons đã tồn tại")
            
            # Kiểm tra cấu trúc bảng comparisons
            cursor.execute("PRAGMA table_info(comparisons)")
            columns = {col[1]: col for col in cursor.fetchall()}
            
            if "conversation_id" not in columns:
                logger.warning("Cột conversation_id không tồn tại trong bảng comparisons, tiến hành sửa chữa...")
                
                # Tạo bảng tạm
                cursor.execute('''
                CREATE TABLE comparisons_temp (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    chosen TEXT NOT NULL,
                    rejected TEXT NOT NULL,
                    chosen_model TEXT NOT NULL,
                    rejected_model TEXT NOT NULL,
                    metadata TEXT
                )
                ''')
                
                try:
                    # Lấy tên của các cột hiện có
                    existing_columns = list(columns.keys())
                    column_str = ", ".join(existing_columns)
                    
                    # Sao chép dữ liệu 
                    cursor.execute(f"INSERT INTO comparisons_temp ({column_str}, conversation_id) SELECT {column_str}, '' FROM comparisons")
                    copy_count = cursor.rowcount
                    logger.info(f"Đã sao chép {copy_count} dòng dữ liệu từ bảng comparisons")
                    
                    # Xóa bảng cũ
                    cursor.execute("DROP TABLE comparisons")
                    
                    # Đổi tên bảng tạm
                    cursor.execute("ALTER TABLE comparisons_temp RENAME TO comparisons")
                    
                    # Tạo lại chỉ mục
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparisons_conversation ON comparisons(conversation_id)')
                    
                    logger.info("Đã sửa chữa thành công bảng comparisons")
                except Exception as e:
                    logger.error(f"Lỗi khi sao chép dữ liệu comparisons: {e}")
        
        # Kiểm tra bảng stats
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stats'")
        stats_exists = cursor.fetchone() is not None
        
        if not stats_exists:
            logger.info("Bảng stats không tồn tại, tạo mới...")
            cursor.execute('''
            CREATE TABLE stats (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                stat_type TEXT NOT NULL,
                value REAL NOT NULL,
                metadata TEXT
            )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_type ON stats(stat_type)')
            logger.info("Đã tạo bảng stats mới")
        else:
            logger.info("Bảng stats đã tồn tại")
        
        conn.commit()
        logger.info("Sửa chữa database hoàn tất thành công!")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi sửa chữa database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function"""
    args = parse_args()
    
    # Thiết lập logging
    global logger
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(log_level)
    
    # In thông tin
    logger.info(f"Bắt đầu sửa chữa database: {args.db}")
    if args.backup:
        logger.info("Sẽ tạo bản sao lưu trước khi sửa chữa")
    if args.force:
        logger.info("Chế độ force được bật: sẽ ghi đè các bảng hiện có nếu cần")
    
    # Sửa chữa database
    success = fix_database_schema(args.db, force=args.force, backup=args.backup)
    
    if success:
        logger.info("Sửa chữa database thành công!")
    else:
        logger.error("Sửa chữa database thất bại!")
        sys.exit(1)

if __name__ == "__main__":
    main()