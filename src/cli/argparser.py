"""
Xử lý tham số dòng lệnh.
Cung cấp cấu hình CLI và phân tích tham số cho hệ thống.
"""

import argparse
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def setup_argparser() -> argparse.ArgumentParser:
    """
    Thiết lập parser tham số dòng lệnh.
    
    Returns:
        Đối tượng ArgumentParser đã cấu hình
    """
    parser = argparse.ArgumentParser(
        description="Hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python main.py -i                                # Chạy ở chế độ tương tác
  python main.py -q "Viết thuật toán sắp xếp"      # Truy vấn đơn
  python main.py -q "Phân tích bài thơ" -g         # Thảo luận nhóm
  python main.py -i -f --auto-model                # Tương tác với thu thập phản hồi
  python main.py --report                          # Hiển thị báo cáo hiệu suất
  python main.py --export-rlhf rlhf_data           # Xuất dữ liệu RLHF
"""
    )
    
    # Các tham số chung
    parser.add_argument('--config', '-c', type=str,
                        help='Đường dẫn tới file cấu hình')
    parser.add_argument('--interactive', '-i', action='store_true', 
                        help='Chạy ở chế độ tương tác')
    parser.add_argument('--query', '-q', type=str,
                        help='Câu hỏi để xử lý (cho chế độ không tương tác)')
    parser.add_argument('--role', '-r', type=str,
                        help='Vai trò mô hình cụ thể để sử dụng')
    parser.add_argument('--temperature', '-t', type=float, default=0.7,
                        help='Nhiệt độ của mô hình (0.0-1.0)')
    parser.add_argument('--max-tokens', '-m', type=int, default=1024,
                        help='Số token tối đa trong phản hồi')
    parser.add_argument('--save', '-s', type=str,
                        help='Tên file để lưu lịch sử hội thoại')
    
    # Tham số thảo luận nhóm
    group_discussion = parser.add_argument_group('Thảo luận nhóm')
    group_discussion.add_argument('--group-discussion', '-g', action='store_true',
                        help='Kích hoạt chế độ thảo luận nhóm giữa các mô hình')
    group_discussion.add_argument('--rounds', type=int, default=2,
                        help='Số vòng thảo luận trong chế độ nhóm (mặc định: 2)')
    group_discussion.add_argument('--verbose', '-v', action='store_true',
                        help='Hiển thị chi tiết quá trình thảo luận (với chế độ nhóm)')
    
    # Tham số RLHF/DPO
    optimization = parser.add_argument_group('Tối ưu hóa RLHF/DPO')
    optimization.add_argument('--feedback', '-f', action='store_true',
                        help='Kích hoạt thu thập phản hồi từ người dùng')
    optimization.add_argument('--no-optimization', action='store_true',
                        help='Tắt tối ưu hóa tự động dựa trên RLHF/DPO')
    optimization.add_argument('--feedback-db', type=str,
                        help='Đường dẫn tới cơ sở dữ liệu phản hồi')
    optimization.add_argument('--export-rlhf', type=str, metavar='DIR',
                        help='Xuất dữ liệu RLHF đã thu thập vào thư mục chỉ định')
    optimization.add_argument('--report', action='store_true',
                        help='Tạo báo cáo hiệu suất mô hình dựa trên phản hồi')
    optimization.add_argument('--auto-model', action='store_true',
                        help='Tự động chọn mô hình tốt nhất dựa trên phân tích câu hỏi')
    optimization.add_argument('--reset-optimization', action='store_true',
                        help='Đặt lại quá trình tối ưu hóa (trọng số về mặc định)')
    optimization.add_argument('--reset-feedback-db', action='store_true',
                        help='Đặt lại cơ sở dữ liệu phản hồi (tạo bản sao lưu trước)')
    
    # Tham số logging
    logging_group = parser.add_argument_group('Logging')
    logging_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Mức độ log')
    logging_group.add_argument('--log-file', type=str,
                        help='Đường dẫn file log (nếu không cung cấp, chỉ log ra console)')
    
    return parser

def parse_args() -> argparse.Namespace:
    """
    Phân tích tham số dòng lệnh.
    
    Returns:
        Đối tượng Namespace chứa các tham số đã phân tích
    """
    parser = setup_argparser()
    args = parser.parse_args()
    
    # Kiểm tra các tham số xung đột
    if args.query is None and not args.interactive and not args.report and not args.export_rlhf and not args.reset_optimization:
        parser.error("Phải cung cấp câu hỏi (--query) hoặc sử dụng chế độ tương tác (--interactive) "
                    "hoặc một trong các chức năng: --report, --export-rlhf, --reset-optimization")
    
    if args.reset_feedback_db and not args.reset_optimization:
        parser.error("--reset-feedback-db chỉ có thể được sử dụng cùng với --reset-optimization")
    
    return args

def args_to_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Chuyển đổi tham số dòng lệnh thành cấu hình hệ thống.
    
    Args:
        args: Đối tượng Namespace chứa các tham số đã phân tích
        
    Returns:
        Dict chứa cấu hình được tạo từ tham số
    """
    config_updates = {
        "system": {}
    }
    
    # Cập nhật cấu hình system
    if args.feedback_db:
        config_updates["system"]["feedback_db"] = args.feedback_db
    
    if args.log_file:
        config_updates["system"]["log_file"] = args.log_file
    
    config_updates["system"]["log_level"] = args.log_level
    
    # Cập nhật cấu hình RLHF/DPO
    config_updates["optimization"] = {
        "enabled": not args.no_optimization,
        "auto_select_model": args.auto_model,
        "feedback": {
            "enabled": args.feedback
        }
    }
    
    # Cập nhật cấu hình thảo luận nhóm
    config_updates["group_discussion"] = {
        "default_rounds": args.rounds
    }
    
    return config_updates

def update_config_from_args(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Cập nhật cấu hình hiện có với các tham số dòng lệnh.
    
    Args:
        config: Cấu hình hiện có
        args: Đối tượng Namespace chứa các tham số đã phân tích
        
    Returns:
        Cấu hình đã được cập nhật
    """
    updates = args_to_config(args)
    
    # Cập nhật nested dict
    def update_nested_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    updated_config = update_nested_dict(config, updates)
    return updated_config