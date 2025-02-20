import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

def fix_database_schema(db_path: str) -> bool:
    """
    Sửa lỗi schema trong database feedback
    
    Args:
        db_path: Đường dẫn đến file database
        
    Returns:
        True nếu sửa thành công, False nếu không
    """
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(db_path):
        logger.error(f"Database không tồn tại: {db_path}")
        return False
    
    conn = None
    try:
        # Sao lưu database trước khi sửa
        backup_path = f"{db_path}.backup"
        
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        logger.info(f"Đã sao lưu database vào {backup_path}")
        
        # Kết nối đến database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Kiểm tra cấu trúc bảng hiện tại
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Kiểm tra xem cột conversation_id có tồn tại không
        if "conversation_id" not in column_names:
            # Tạo bảng tạm để lưu dữ liệu
            cursor.execute("CREATE TABLE feedback_temp AS SELECT * FROM feedback")
            
            # Xóa bảng cũ
            cursor.execute("DROP TABLE feedback")
            
            # Tạo lại bảng với cấu trúc đúng
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
            
            # Di chuyển dữ liệu từ bảng tạm sang bảng mới nếu có dữ liệu
            cursor.execute("PRAGMA table_info(feedback_temp)")
            temp_columns = cursor.fetchall()
            temp_column_names = [col[1] for col in temp_columns]
            
            if temp_column_names:
                # Tìm các cột chung giữa hai bảng
                common_columns = [col for col in temp_column_names if col in column_names]
                common_columns_str = ", ".join(common_columns)
                
                # Copy dữ liệu, đặt conversation_id mặc định là empty string
                try:
                    cursor.execute(f"INSERT INTO feedback ({common_columns_str}, conversation_id) SELECT {common_columns_str}, '' FROM feedback_temp")
                    logger.info(f"Đã di chuyển {cursor.rowcount} bản ghi từ bảng tạm")
                except Exception as e:
                    logger.error(f"Lỗi khi di chuyển dữ liệu: {e}")
            
            # Xóa bảng tạm
            cursor.execute("DROP TABLE feedback_temp")
            
            # Tạo lại chỉ mục
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON feedback(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)')
            
            conn.commit()
            logger.info("Đã sửa cấu trúc bảng feedback, thêm cột conversation_id")
        
        # Kiểm tra bảng comparisons
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comparisons'")
        if not cursor.fetchone():
            # Tạo bảng comparisons nếu chưa tồn tại
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
            conn.commit()
            logger.info("Đã tạo bảng comparisons")
        
        # Kiểm tra bảng stats
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stats'")
        if not cursor.fetchone():
            # Tạo bảng stats nếu chưa tồn tại
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
            conn.commit()
            logger.info("Đã tạo bảng stats")
        
        logger.info("Đã hoàn thành sửa chữa cấu trúc database")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi sửa chữa database: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Script để chạy trực tiếp nếu cần
if __name__ == "__main__":
    # Thiết lập logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Đường dẫn mặc định
    default_db_path = "data/feedback.db"
    
    # Kiểm tra xem có đường dẫn được cung cấp không
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db_path
    
    # Sửa chữa database
    if fix_database_schema(db_path):
        print(f"Đã sửa chữa database thành công: {db_path}")
    else:
        print(f"Không thể sửa chữa database: {db_path}")