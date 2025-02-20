# Makefile
.PHONY: setup run run-interactive performance-report export-rlhf docker-build docker-run docker-interactive clean test

# Cài đặt môi trường
setup:
	pip install -r requirements.txt
	mkdir -p data/conversations data/rlhf_exports logs

# Chạy với câu hỏi
run:
	python main.py --query "$(QUERY)" $(ARGS)

# Chạy ở chế độ tương tác
run-interactive:
	python main.py --interactive --feedback $(ARGS)

# Tạo báo cáo hiệu suất
performance-report:
	python main.py --performance-report

# Xuất dữ liệu RLHF
export-rlhf:
	python main.py --export-rlhf data/rlhf_exports

# Thảo luận nhóm
group-discussion:
	python main.py --query "$(QUERY)" --group-discussion --rounds 3 --verbose

# Xây dựng Docker image
docker-build:
	docker-compose build

# Chạy với Docker
docker-run:
	docker-compose run --rm assistant --query "$(QUERY)" $(ARGS)

# Chạy chế độ tương tác với Docker
docker-interactive:
	docker-compose run --rm assistant --interactive --feedback $(ARGS)

# Dọn dẹp
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

# Chạy kiểm thử
test:
	pytest tests/
