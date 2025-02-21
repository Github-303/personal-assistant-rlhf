#!/bin/bash

# Script chạy hệ thống hỗ trợ cá nhân nâng cao

# Kiểm tra Ollama
echo "Kiểm tra kết nối với Ollama..."
curl -s http://localhost:11434/api/version > /dev/null
if [ $? -ne 0 ]; then
    echo "CẢNH BÁO: Không thể kết nối với Ollama. Vui lòng đảm bảo Ollama đang chạy."
    echo "Bạn có muốn tiếp tục không? (y/n)"
    read response
    if [ "$response" != "y" ]; then
        echo "Thoát."
        exit 1
    fi
fi

# Tạo thư mục cần thiết
mkdir -p data/conversations data/rlhf_exports logs

# Kiểm tra và khởi tạo môi trường ảo nếu cần
if [ ! -d "venv" ]; then
    echo "Khởi tạo môi trường ảo..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Hiển thị menu
show_menu() {
    clear
    echo "====================================================="
    echo "  HỆ THỐNG HỖ TRỢ CÁ NHÂN NÂNG CAO VỚI RLHF VÀ DPO  "
    echo "====================================================="
    echo "1. Chế độ tương tác (với thu thập phản hồi)"
    echo "2. Chế độ tương tác (không thu thập phản hồi)"
    echo "3. Chế độ tương tác + Thảo luận nhóm"
    echo "4. Nhập câu hỏi cụ thể"
    echo "5. Báo cáo hiệu suất mô hình"
    echo "6. Xuất dữ liệu RLHF"
    echo "7. Đặt lại tối ưu hóa"
    echo "8. Thoát"
    echo "====================================================="
    echo "Lựa chọn của bạn: "
}

run_interactive() {
    python main.py --interactive --feedback --auto-model
}

run_interactive_no_feedback() {
    python main.py --interactive --no-optimization
}

run_interactive_group() {
    python main.py --interactive --feedback --auto-model --group-discussion
}

run_single_query() {
    echo "Nhập câu hỏi của bạn:"
    read -e query
    echo "Sử dụng thảo luận nhóm? (y/n) [n]:"
    read use_group
    
    if [ "$use_group" = "y" ]; then
        python main.py --query "$query" --auto-model --group-discussion --feedback
    else
        python main.py --query "$query" --auto-model --feedback
    fi
    
    echo "Nhấn Enter để tiếp tục..."
    read
}

show_report() {
    python main.py --report
    echo "Nhấn Enter để tiếp tục..."
    read
}

export_rlhf() {
    echo "Xuất dữ liệu RLHF ra thư mục data/rlhf_exports"
    python main.py --export-rlhf data/rlhf_exports
    echo "Nhấn Enter để tiếp tục..."
    read
}

reset_optimization() {
    echo "CẢNH BÁO: Điều này sẽ đặt lại tất cả trọng số tối ưu hóa về giá trị mặc định."
    echo "Bạn có chắc chắn muốn tiếp tục không? (y/n)"
    read confirm
    
    if [ "$confirm" = "y" ]; then
        python main.py --reset-optimization --confirmed
        echo "Đã đặt lại tối ưu hóa."
    else
        echo "Đã hủy."
    fi
    
    echo "Nhấn Enter để tiếp tục..."
    read
}

# Main loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1) run_interactive ;;
        2) run_interactive_no_feedback ;;
        3) run_interactive_group ;;
        4) run_single_query ;;
        5) show_report ;;
        6) export_rlhf ;;
        7) reset_optimization ;;
        8) echo "Tạm biệt!"; break ;;
        *) echo "Lựa chọn không hợp lệ"; sleep 1 ;;
    esac
done

# Deactivate virtual environment
deactivate
