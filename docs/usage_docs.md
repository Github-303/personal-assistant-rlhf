# Hướng dẫn sử dụng chi tiết

Tài liệu này cung cấp hướng dẫn sử dụng chi tiết cho hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO.

## Cài đặt và thiết lập

### Yêu cầu

- Python 3.8+
- Ollama đã được cài đặt (https://ollama.com/download)
- Các thư viện phụ thuộc (xem `requirements.txt`)

### Cài đặt

```bash
# Clone repository
git clone https://github.com/github-303/personal-assistant-rlhf
cd personal-assistant-rlhf

# Cài đặt dependencies
pip install -r requirements.txt

# Hoặc cài đặt dưới dạng package
pip install -e .
```

### Khởi động Ollama

```bash
# Khởi động Ollama server (nếu chưa chạy)
ollama serve
```

### Cấu hình

Hệ thống sử dụng các file YAML trong thư mục `config/` để cấu hình:

- `default.yml`: Cấu hình chung
- `models.yml`: Cấu hình mô hình
- `optimization.yml`: Cấu hình RLHF/DPO
- `prompt_templates.yml`: Mẫu prompt

## Sử dụng cơ bản

### Chạy ở chế độ tương tác

```bash
python main.py --interactive
```

Trong chế độ tương tác, bạn có thể gõ câu hỏi và nhận phản hồi từ hệ thống. Để thoát, nhập `exit`, `quit` hoặc `thoát`.

### Chạy với một câu hỏi cụ thể

```bash
python main.py --query "Viết một hàm Python để tìm số Fibonacci"
```

### Sử dụng mô hình cụ thể

```bash
python main.py --query "Viết một hàm Python để tìm số Fibonacci" --role code
```

Các vai trò có sẵn:
- `code`: Mô hình chuyên về lập trình (Qwen2.5-coder 7B)
- `deep_thinking`: Mô hình chuyên về tư duy sâu (DeepSeek-r1 8B)
- `llm`: Mô hình nhỏ gọn và nhanh (DeepSeek-r1 1.5B)

### Sử dụng thảo luận nhóm

```bash
python main.py --query "So sánh các phương pháp học máy khác nhau" --group-discussion
```

Thêm tham số `--verbose` để xem chi tiết quá trình thảo luận:

```bash
python main.py --query "So sánh các phương pháp học máy khác nhau" --group-discussion --verbose
```

### Điều chỉnh tham số sinh văn bản

```bash
python main.py --query "Viết một câu chuyện ngắn" --temperature 0.9 --max-tokens 2048
```

## Sử dụng RLHF và DPO

### Kích hoạt thu thập phản hồi

```bash
python main.py --interactive --feedback
```

Khi kích hoạt thu thập phản hồi, hệ thống sẽ thỉnh thoảng yêu cầu bạn đánh giá câu trả lời hoặc so sánh giữa các câu trả lời.

### Tự động chọn mô hình tốt nhất

```bash
python main.py --query "Phân tích lợi ích của năng lượng tái tạo" --auto-model
```

Tham số `--auto-model` cho phép hệ thống tự động chọn mô hình tốt nhất dựa trên phân tích câu hỏi và phản hồi trước đó.

### Xem báo cáo hiệu suất

```bash
python main.py --report
```

Lệnh này hiển thị báo cáo chi tiết về hiệu suất của các mô hình dựa trên phản hồi đã thu thập.

### Xuất dữ liệu RLHF

```bash
python main.py --export-rlhf data/exports
```

Xuất dữ liệu RLHF đã thu thập để sử dụng huấn luyện lại mô hình.

### Đặt lại quá trình tối ưu hóa

```bash
python main.py --reset-optimization
```

Đặt lại tất cả trọng số tối ưu hóa về giá trị mặc định. Thêm `--reset-feedback-db` để xóa toàn bộ dữ liệu phản hồi (sẽ tạo bản sao lưu trước).

## Tùy chọn nâng cao

### Log và gỡ lỗi

```bash
python main.py --interactive --log-level DEBUG --log-file logs/debug.log
```

### Lưu lịch sử hội thoại

```bash
python main.py --interactive --save my_conversation.json
```

### Sử dụng file cấu hình tùy chỉnh

```bash
python main.py --interactive --config path/to/custom/config.yml
```

## Chế độ tương tác

Trong chế độ tương tác, bạn có thể sử dụng các lệnh đặc biệt:

| Lệnh | Mô tả |
|------|-------|
| `help` | Hiển thị danh sách lệnh |
| `toggle-opt` | Bật/tắt tối ưu hóa tự động |
| `toggle-feedback` | Bật/tắt thu thập phản hồi |
| `toggle-auto-model` | Bật/tắt tự động chọn mô hình |
| `report` | Hiển thị báo cáo hiệu suất |
| `export-rlhf [thư_mục]` | Xuất dữ liệu RLHF |
| `save [tên_file]` | Lưu lịch sử hội thoại |
| `status` | Hiển thị trạng thái hệ thống |
| `clear` | Xóa màn hình |
| `reset` | Đặt lại trọng số tối ưu hóa |
| `exit` / `quit` / `thoát` | Thoát chương trình |

## Docker

### Xây dựng và chạy với Docker

```bash
# Xây dựng image
docker-compose build

# Chạy ở chế độ tương tác
docker-compose run --rm assistant --interactive --feedback

# Chạy với câu hỏi cụ thể
docker-compose run --rm assistant --query "Phân tích tác động của AI" --group-discussion
```

### Sửa đổi cấu hình Docker

Bạn có thể điều chỉnh `docker-compose.yml` để thay đổi cấu hình:

```yaml
# Thay đổi biến môi trường
environment:
  - OLLAMA_HOST=ollama
  - OLLAMA_PORT=11434
  - LOG_LEVEL=DEBUG
  - FEEDBACK_ENABLED=true
```

## Hiểu về phản hồi RLHF

### Đánh giá số (1-5 sao)

Khi được yêu cầu, bạn có thể đánh giá câu trả lời theo thang điểm từ 1 đến 5:
- **1**: Rất kém, không có giá trị
- **2**: Kém, có một số thông tin nhưng không đủ
- **3**: Trung bình, đáp ứng được yêu cầu cơ bản
- **4**: Tốt, thông tin chính xác và đầy đủ
- **5**: Rất tốt, vượt trội, đầy đủ và sâu sắc

### So sánh phản hồi

Khi được yêu cầu so sánh, bạn sẽ thấy nhiều phản hồi khác nhau và chọn phản hồi tốt nhất. Hệ thống sẽ sử dụng thông tin này để điều chỉnh trọng số cho các mô hình.

## Mẹo và thủ thuật

### Tối ưu hóa hiệu suất

1. **Thu thập đủ phản hồi**: Hệ thống hoạt động tốt hơn khi có nhiều phản hồi
2. **Sử dụng đúng vai trò**: Chọn vai trò phù hợp cho từng loại câu hỏi
3. **Điều chỉnh nhiệt độ**: Sử dụng nhiệt độ thấp (0.1-0.3) cho câu trả lời chính xác, nhiệt độ cao (0.7-0.9) cho nội dung sáng tạo

### Tối ưu hóa thảo luận nhóm

1. **Số vòng phù hợp**: 2-3 vòng là đủ cho hầu hết các câu hỏi
2. **Chọn các mô hình đa dạng**: Thảo luận nhóm hiệu quả nhất khi các mô hình có điểm mạnh khác nhau
3. **Sử dụng verbose**: Theo dõi quá trình thảo luận để hiểu cách các mô hình tương tác

### Khắc phục sự cố

1. **Kiểm tra Ollama**: Đảm bảo Ollama đang chạy (`ollama serve`)
2. **Kiểm tra mô hình**: Đảm bảo các mô hình đã được tải (`ollama list`)
3. **Xem log**: Sử dụng `--log-level DEBUG` để xem thông tin chi tiết
4. **Xóa cache**: Thử xóa thư mục `.cache/ollama` nếu gặp vấn đề với mô hình

## Các kịch bản sử dụng phổ biến

### 1. Lập trình và giải thuật

```bash
python main.py --query "Viết một thuật toán sắp xếp nhanh bằng Python" --role code
```

### 2. Phân tích chiến lược và tư duy phản biện

```bash
python main.py --query "Phân tích ưu nhược điểm của mô hình kinh doanh SaaS" --role deep_thinking
```

### 3. Tóm tắt và thông tin ngắn gọn

```bash
python main.py --query "Tóm tắt ngắn gọn về cách hoạt động của blockchain" --role llm
```

### 4. Vấn đề phức tạp đa chiều

```bash
python main.py --query "Phân tích tác động của AI đối với thị trường lao động và đề xuất giải pháp" --group-discussion
```

### 5. Thu thập dữ liệu cho RLHF

```bash
python main.py --interactive --feedback --auto-model
# Sử dụng hệ thống và cung cấp phản hồi
# Sau đó xuất dữ liệu
python main.py --export-rlhf data/my_rlhf_dataset
```

## Kết luận

Hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO cung cấp trải nghiệm trợ lý thông minh, liên tục cải thiện dựa trên phản hồi của bạn. Bằng cách kết hợp nhiều mô hình với cơ chế thảo luận nhóm và tối ưu hóa thông minh, hệ thống mang lại câu trả lời chất lượng cao và cá nhân hóa theo thời gian.
