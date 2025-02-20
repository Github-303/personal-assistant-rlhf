# Đóng góp cho Hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO

Cảm ơn bạn đã quan tâm đến việc đóng góp cho dự án của chúng tôi! Mọi đóng góp đều được đánh giá cao.

## Quy trình đóng góp

1. Fork repository
2. Tạo branch mới: `git checkout -b feature/your-feature-name`
3. Commit các thay đổi: `git commit -am 'Add some feature'`
4. Push lên branch của bạn: `git push origin feature/your-feature-name`
5. Tạo Pull Request

## Tiêu chuẩn mã nguồn

- Sử dụng [Black](https://github.com/psf/black) để định dạng mã nguồn
- Tuân thủ [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Viết docstrings theo định dạng Google
- Sử dụng type hints
- Đảm bảo độ phủ kiểm thử ít nhất 80%

## Quy trình phát triển

1. Tạo issue trước khi bắt đầu làm việc trên một tính năng mới
2. Thảo luận thiết kế và cách tiếp cận trong issue
3. Viết kiểm thử đơn vị cho mã nguồn mới
4. Đảm bảo tất cả kiểm thử đều pass
5. Cập nhật tài liệu nếu cần

## Cấu trúc thư mục

Vui lòng tuân thủ cấu trúc thư mục hiện tại:

```
personal-assistant-rlhf/
├── src/
│   ├── core/           # Lõi hệ thống
│   ├── optimization/   # Mô-đun tối ưu hóa RLHF/DPO
│   ├── integration/    # Tích hợp các thành phần
│   ├── cli/            # Giao diện dòng lệnh
│   └── utils/          # Các tiện ích
│
├── config/             # Cấu hình
├── data/               # Dữ liệu
└── tests/              # Kiểm thử
```

## Hướng dẫn push commits

- Sử dụng commit messages rõ ràng và mô tả
- Sử dụng các prefixes sau:
  - `feat:` cho tính năng mới
  - `fix:` cho bug fixes
  - `docs:` cho thay đổi tài liệu
  - `test:` cho việc thêm kiểm thử
  - `refactor:` cho refactoring mã nguồn
  - `chore:` cho thay đổi build/tools

Ví dụ: `feat: Add comparative feedback collection for RLHF`

## Kiểm thử

- Viết kiểm thử đơn vị cho tất cả mã nguồn mới
- Đảm bảo kiểm thử tích hợp cho các thành phần lớn
- Chạy kiểm thử trước khi tạo Pull Request:

```bash
# Chạy tất cả kiểm thử
pytest

# Kiểm tra độ phủ
pytest --cov=src tests/
```

## Báo cáo lỗi

Khi báo cáo lỗi, vui lòng bao gồm:

- Mô tả rõ ràng về vấn đề
- Các bước tái tạo lỗi
- Môi trường (hệ điều hành, phiên bản Python, phiên bản các thư viện)
- Log lỗi (nếu có)
- Giải pháp đề xuất (nếu có)

## Tài liệu

- Cập nhật tài liệu khi thêm/thay đổi tính năng
- Viết docstrings cho tất cả các lớp và hàm mới
- Cập nhật README.md nếu cần

## Cấp phép

Bằng cách đóng góp, bạn đồng ý rằng đóng góp của bạn sẽ được cấp phép theo giấy phép MIT của dự án.

## Liên hệ

Nếu bạn có câu hỏi, vui lòng tạo issue hoặc liên hệ với chúng tôi qua email: contact@example.com
