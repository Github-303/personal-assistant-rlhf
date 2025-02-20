# #!/usr/bin/env python
# """
# Điểm vào chính cho hệ thống trợ lý cá nhân với RLHF và DPO
# """

# import os
# import sys
# import time
# import logging
# import argparse
# from typing import Optional

# # Thêm thư mục gốc vào đường dẫn để import
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from src.integration.interfaces import setup_assistant
# from src.cli.interactive import InteractiveShell
# from src.cli.setup import setup_logging

# def main():
#     """Hàm main"""
#     start_time = time.time()
    
#     # Phân tích tham số dòng lệnh
#     parser = argparse.ArgumentParser(description="Hệ thống trợ lý cá nhân với RLHF và DPO")
#     parser.add_argument("--config", "-c", type=str, help="Đường dẫn đến file cấu hình")
#     parser.add_argument("--interactive", "-i", action="store_true", help="Khởi động chế độ tương tác")
#     parser.add_argument("--no-optimization", action="store_true", help="Tắt tối ưu hóa")
#     parser.add_argument("--no-auto-model", action="store_true", help="Tắt tự động chọn mô hình")
#     parser.add_argument("--no-feedback", action="store_true", help="Tắt thu thập phản hồi")
#     parser.add_argument("--feedback", action="store_true", help="Bật thu thập phản hồi")
#     parser.add_argument("--auto-model", action="store_true", help="Bật tự động chọn mô hình")
#     parser.add_argument("--api", action="store_true", help="Khởi động API server")
#     parser.add_argument("--port", type=int, default=8000, help="Port cho API server")
#     parser.add_argument("--host", type=str, default="127.0.0.1", help="Host cho API server")
#     parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
#                         default="INFO", help="Mức độ ghi log")
#     parser.add_argument("--export-feedback", action="store_true", help="Xuất dữ liệu phản hồi")
#     parser.add_argument("--export-dir", type=str, help="Thư mục xuất dữ liệu phản hồi")
#     parser.add_argument("--model", type=str, help="Chỉ định mô hình cụ thể để sử dụng")
#     parser.add_argument("--group-discussion", action="store_true", help="Bật chế độ thảo luận nhóm")
#     parser.add_argument("--no-group-discussion", action="store_true", help="Tắt chế độ thảo luận nhóm")
#     args = parser.parse_args()
    
#     # Thiết lập logging
#     log_level = getattr(logging, args.log_level)
#     setup_logging(log_level)
#     logger = logging.getLogger("main")
    
#     try:
#         # Khởi tạo trợ lý
#         assistant = setup_assistant(args.config)
        
#         # Cấu hình trợ lý dựa trên tham số dòng lệnh
#         if args.no_optimization:
#             assistant.toggle_optimization(False)
            
#         if args.no_auto_model:
#             assistant.toggle_auto_select_model(False)
#         elif args.auto_model:
#             assistant.toggle_auto_select_model(True)
            
#         if args.no_feedback:
#             assistant.toggle_feedback_collection(False)
#         elif args.feedback:
#             assistant.toggle_feedback_collection(True)
            
#         if args.group_discussion:
#             assistant.toggle_group_discussion(True)
#         elif args.no_group_discussion:
#             assistant.toggle_group_discussion(False)
            
#         initialization_time = time.time() - start_time
#         logger.info(f"Khởi động hoàn tất trong {initialization_time:.2f}s")
        
#         # Xuất dữ liệu phản hồi nếu được yêu cầu
#         if args.export_feedback:
#             export_path = assistant.export_feedback_data(args.export_dir)
#             logger.info(f"Đã xuất dữ liệu phản hồi đến {export_path}")
#             return
            
#         # Khởi động API server nếu được yêu cầu
#         if args.api:
#             from src.api.server import start_api_server
#             start_api_server(assistant, host=args.host, port=args.port)
#             return
            
#         # Khởi động shell tương tác nếu được yêu cầu
#         if args.interactive:
#             shell = InteractiveShell(assistant, model_name=args.model)
#             shell.run()
#         else:
#             # Mặc định là chế độ tương tác
#             shell = InteractiveShell(assistant, model_name=args.model)
#             shell.run()
            
#     except KeyboardInterrupt:
#         logger.info("Đã nhận tín hiệu ngắt, thoát...")
#     except Exception as e:
#         logger.error(f"Lỗi không mong đợi: {e}", exc_info=True)
#     finally:
#         total_time = time.time() - start_time
#         logger.info(f"Tổng thời gian chạy: {total_time:.2f}s")

# if __name__ == "__main__":
#     main()
#     parser.add_

#!/usr/bin/env python
"""
Điểm vào chính cho hệ thống trợ lý cá nhân với RLHF và DPO
"""

import os
import sys
import time
import logging
import argparse
from typing import Optional

# Thêm thư mục gốc vào đường dẫn để import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integration.interfaces import setup_assistant
from src.cli.interactive import InteractiveShell
from src.cli.setup import setup_logging

def parse_arguments():
    """Phân tích tham số dòng lệnh"""
    parser = argparse.ArgumentParser(description="Hệ thống trợ lý cá nhân với RLHF và DPO")
    parser.add_argument("--config", "-c", type=str, help="Đường dẫn đến file cấu hình")
    parser.add_argument("--interactive", "-i", action="store_true", help="Khởi động chế độ tương tác")
    parser.add_argument("--no-optimization", action="store_true", help="Tắt tối ưu hóa")
    parser.add_argument("--no-auto-model", action="store_true", help="Tắt tự động chọn mô hình")
    parser.add_argument("--no-feedback", action="store_true", help="Tắt thu thập phản hồi")
    parser.add_argument("--feedback", action="store_true", help="Bật thu thập phản hồi")
    parser.add_argument("--auto-model", action="store_true", help="Bật tự động chọn mô hình")
    parser.add_argument("--api", action="store_true", help="Khởi động API server")
    parser.add_argument("--port", type=int, default=8000, help="Port cho API server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host cho API server")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="INFO", help="Mức độ ghi log")
    parser.add_argument("--export-feedback", action="store_true", help="Xuất dữ liệu phản hồi")
    parser.add_argument("--export-dir", type=str, help="Thư mục xuất dữ liệu phản hồi")
    parser.add_argument("--model", type=str, help="Chỉ định mô hình cụ thể để sử dụng")
    parser.add_argument("--group-discussion", action="store_true", help="Bật chế độ thảo luận nhóm")
    parser.add_argument("--no-group-discussion", action="store_true", help="Tắt chế độ thảo luận nhóm")
    
    return parser.parse_args()

def main():
    """Hàm main"""
    start_time = time.time()
    
    # Phân tích tham số dòng lệnh
    args = parse_arguments()
    
    # Thiết lập logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    logger = logging.getLogger("main")
    
    try:
        # Khởi tạo trợ lý
        assistant = setup_assistant(args.config)
        
        # Cấu hình trợ lý dựa trên tham số dòng lệnh
        if args.no_optimization:
            assistant.toggle_optimization(False)
            
        if args.no_auto_model:
            assistant.toggle_auto_select_model(False)
        elif args.auto_model:
            assistant.toggle_auto_select_model(True)
            
        if args.no_feedback:
            assistant.toggle_feedback_collection(False)
        elif args.feedback:
            assistant.toggle_feedback_collection(True)
            
        if args.group_discussion:
            assistant.toggle_group_discussion(True)
        elif args.no_group_discussion:
            assistant.toggle_group_discussion(False)
            
        initialization_time = time.time() - start_time
        logger.info(f"Khởi động hoàn tất trong {initialization_time:.2f}s")
        
        # Xuất dữ liệu phản hồi nếu được yêu cầu
        if args.export_feedback:
            export_path = assistant.export_feedback_data(args.export_dir)
            logger.info(f"Đã xuất dữ liệu phản hồi đến {export_path}")
            return
            
        # Khởi động API server nếu được yêu cầu
        if args.api:
            from src.api.server import start_api_server
            start_api_server(assistant, host=args.host, port=args.port)
            return
            
        # Khởi động shell tương tác nếu được yêu cầu
        if args.interactive:
            shell = InteractiveShell(assistant)
            if args.model:
                shell.model_name = args.model
            shell.run()
        else:
            # Mặc định là chế độ tương tác
            shell = InteractiveShell(assistant)
            if args.model:
                shell.model_name = args.model
            shell.run()
            
    except KeyboardInterrupt:
        logger.info("Đã nhận tín hiệu ngắt, thoát...")
    except Exception as e:
        logger.error(f"Lỗi không mong đợi: {e}", exc_info=True)
    finally:
        total_time = time.time() - start_time
        logger.info(f"Tổng thời gian chạy: {total_time:.2f}s")

if __name__ == "__main__":
    main()