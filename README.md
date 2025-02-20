# Hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO

Một trợ lý cá nhân thông minh sử dụng ba mô hình Ollama (Qwen 2.5, DeepSeek-8B và DeepSeek-1.5B) với khả năng tự cải thiện dựa trên phản hồi người dùng thông qua kỹ thuật RLHF (Reinforcement Learning from Human Feedback) và DPO (Direct Preference Optimization).

## Tính năng chính

- **Sử dụng ba mô hình chuyên biệt**:
  - **Qwen2.5-coder:7b** - Chuyên về lập trình và code
  - **DeepSeek-r1:8B** - Chuyên về tư duy sâu và phân tích
  - **DeepSeek-r1:1.5B** - Mô hình nhỏ gọn, nhanh và hiệu quả

- **Thảo luận nhóm thông minh**: Các mô hình thảo luận qua nhiều vòng để đưa ra câu trả lời tối ưu

- **Tối ưu hóa từ phản hồi người dùng**:
  - RLHF: Cải thiện dựa trên đánh giá số (1-5 sao)
  - DPO: Cải thiện dựa trên sở thích (A tốt hơn B)

- **Tự động phân tích câu hỏi**: Tự động chọn mô hình phù hợp nhất với từng loại câu hỏi

- **Tối ưu hóa prompt**: Tùy chỉnh prompt và system prompt dựa trên phản hồi

## Yêu cầu hệ thống

- Python 3.8+
- [Ollama](https://ollama.com/download) đã được cài đặt và chạy
- Các mô hình Ollama: qwen2 .5-coder:7b, deepseek-r1:8b, deepseek-r1:1.5b

## Cài đặt

```bash
# Clone repository
git clone https://github.com/github-303/personal-assistant-rlhf
cd personal-assistant-rlhf

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt package
pip install -e .
```

## Sử dụng cơ bản

### Chế độ tương tác

```bash
python main.py --interactive --feedback
```

### Truy vấn đơn với tự động chọn mô hình

```bash
python main.py --query "Thiết kế một kiến trúc microservice cho ứng dụng thương mại điện tử" --auto-model
```

### Thảo luận nhóm

```bash
python main.py --query "Phân tích ưu nhược điểm của các framework JavaScript" --group-discussion
```

## Tùy chọn dòng lệnh

### Tùy chọn chính

| Tùy chọn | Mô tả |
|----------|-------|
| `--interactive`, `-i` | Chạy ở chế độ tương tác |
| `--query TEXT`, `-q TEXT` | Câu hỏi để xử lý |
| `--role ROLE`, `-r ROLE` | Chọn mô hình cụ thể (code/deep_thinking/llm) |
| `--temperature FLOAT`, `-t FLOAT` | Nhiệt độ của mô hình (0.0-1.0) |
| `--max-tokens INT`, `-m INT` | Số token tối đa trong phản hồi |

### Tùy chọn thảo luận nhóm

| Tùy chọn | Mô tả |
|----------|-------|
| `--group-discussion`, `-g` | Kích hoạt chế độ thảo luận nhóm |
| `--rounds INT` | Số vòng thảo luận (mặc định: 2) |
| `--verbose`, `-v` | Hiển thị chi tiết quá trình thảo luận |

### Tùy chọn RLHF/DPO

| Tùy chọn | Mô tả |
|----------|-------|
| `--feedback`, `-f` | Kích hoạt thu thập phản hồi |
| `--no-optimization` | Tắt tối ưu hóa tự động |
| `--auto-model` | Tự động chọn mô hình tốt nhất |
| `--report` | Hiển thị báo cáo hiệu suất |
| `--export-rlhf DIR` | Xuất dữ liệu RLHF |
| `--reset-optimization` | Đặt lại trọng số về mặc định |

## Cấu trúc dự án

```
personal-assistant-rlhf/
├── src/                              # Thư mục mã nguồn chính
│   ├── core/                         # Lõi hệ thống
│   │   ├── models.py                 # Quản lý mô hình Ollama
│   │   ├── assistant.py              # Hệ thống trợ lý cơ bản
│   │   └── group_discussion.py       # Thảo luận nhóm
│   │
│   ├── optimization/                 # Mô-đun tối ưu hóa RLHF/DPO
│   │   ├── feedback_store.py         # Lưu trữ và quản lý phản hồi
│   │   ├── preference_optimizer.py   # Tối ưu hóa sở thích (DPO)
│   │   ├── feedback_collector.py     # Thu thập phản hồi (RLHF)
│   │   ├── response_optimizer.py     # Tối ưu hóa câu trả lời
│   │   └── manager.py                # Quản lý tối ưu hóa
│   │
│   ├── integration/                  # Tích hợp các thành phần
│   │   ├── enhanced_assistant.py     # Trợ lý nâng cao với RLHF/DPO
│   │   └── interfaces.py             # Giao diện chung
│   │
│   ├── cli/                          # Giao diện dòng lệnh
│   │   ├── argparser.py              # Xử lý tham số dòng lệnh
│   │   ├── interactive.py            # Chế độ tương tác
│   │   └── reporting.py              # Báo cáo hiệu suất
│   │
│   └── utils/                        # Các tiện ích
│       ├── logging_setup.py          # Cấu hình logging
│       ├── prompt_templates.py       # Các mẫu prompt
│       └── export.py                 # Xuất dữ liệu
│
├── config/                           # Cấu hình
│   ├── default.yml                   # Cấu hình mặc định
│   ├── models.yml                    # Cấu hình mô hình
│   ├── optimization.yml              # Cấu hình tối ưu hóa
│   └── prompt_templates.yml          # Mẫu prompt
│
├── data/                             # Dữ liệu
│   ├── feedback.db                   # Cơ sở dữ liệu phản hồi
│   ├── conversations/                # Lịch sử hội thoại
│   └── rlhf_exports/                 # Dữ liệu RLHF xuất ra
│
├── main.py                           # Điểm vào chính
└── setup.py                          # Cấu hình cài đặt
```

## Lệnh đặc biệt trong chế độ tương tác

Khi ở chế độ tương tác, bạn có thể sử dụng các lệnh đặc biệt:

| Lệnh | Chức năng |
|------|-----------|
| `help` | Hiển thị trợ giúp |
| `toggle-opt` | Bật/tắt tối ưu hóa tự động |
| `toggle-feedback` | Bật/tắt thu thập phản hồi |
| `toggle-auto-model` | Bật/tắt tự động chọn mô hình |
| `report` | Hiển thị báo cáo hiệu suất |
| `export-rlhf [dir]` | Xuất dữ liệu RLHF |
| `save [file]` | Lưu lịch sử hội thoại |
| `status` | Hiển thị trạng thái hệ thống |

## Docker

Bạn có thể chạy hệ thống trong Docker:

```bash
# Xây dựng image
docker-compose build

# Chạy chế độ tương tác
docker-compose run --rm assistant --interactive --feedback

# Chạy truy vấn đơn
docker-compose run --rm assistant --query "Viết thuật toán sắp xếp nhanh" --auto-model
```

## RLHF và DPO

Hệ thống sử dụng hai kỹ thuật chính để học từ phản hồi người dùng:

1. **RLHF (Reinforcement Learning from Human Feedback)**:
   - Thu thập đánh giá số (1-5 sao) cho câu trả lời
   - Sử dụng điểm số để điều chỉnh trọng số mô hình
   - Cải thiện hiệu suất theo thời gian

2. **DPO (Direct Preference Optimization)**:
   - Thu thập so sánh giữa hai câu trả lời (A tốt hơn B)
   - Xây dựng ma trận ưu tiên (mô hình nào tốt hơn cho từng loại câu hỏi)
   - Tối ưu hóa việc lựa chọn mô hình và tham số

## Đóng góp

Đóng góp luôn được hoan nghênh! Vui lòng xem [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết.

## Giấy phép

Dự án này được cấp phép theo giấy phép MIT - xem file [LICENSE](LICENSE) để biết thêm chi tiết.