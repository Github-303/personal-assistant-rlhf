#!/usr/bin/env python
"""
Script thiết lập môi trường cho hệ thống trợ lý cá nhân
Thực hiện:
1. Cài đặt các thư viện phụ thuộc
2. Tạo các thư mục cần thiết
3. Tạo file cấu hình mặc định
4. Thiết lập môi trường phát triển
"""

import os
import sys
import subprocess
import argparse
import logging
import shutil
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Thêm thư mục gốc vào đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Thiết lập môi trường cho hệ thống trợ lý cá nhân")
    parser.add_argument("--config-dir", type=str, default="config",
                        help="Thư mục chứa cấu hình")
    parser.add_argument("--data-dir", type=str, default="data",
                        help="Thư mục chứa dữ liệu")
    parser.add_argument("--logs-dir", type=str, default="logs",
                        help="Thư mục chứa log")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434",
                        help="URL của Ollama API")
    parser.add_argument("--dev", action="store_true",
                        help="Thiết lập môi trường phát triển")
    parser.add_argument("--force", action="store_true",
                        help="Ghi đè các file cấu hình hiện có")
    parser.add_argument("--no-deps", action="store_true",
                        help="Không cài đặt các thư viện phụ thuộc")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Mức độ ghi log")
    
    return parser.parse_args()

def setup_logging(log_level: str) -> logging.Logger:
    """
    Thiết lập logging
    
    Args:
        log_level: Mức độ ghi log
        
    Returns:
        Đối tượng logger
    """
    # Chuyển đổi tên level thành giá trị
    numeric_level = getattr(logging, log_level)
    
    # Định dạng log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Thiết lập logging
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler()]
    )
    
    return logging.getLogger("setup")

def create_directories(dirs: List[str], logger: logging.Logger) -> None:
    """
    Tạo các thư mục cần thiết
    
    Args:
        dirs: Danh sách thư mục cần tạo
        logger: Đối tượng logger
    """
    for dir_path in dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Đã tạo thư mục: {dir_path}")
            else:
                logger.debug(f"Thư mục đã tồn tại: {dir_path}")
        except Exception as e:
            logger.error(f"Lỗi khi tạo thư mục {dir_path}: {e}")

def install_dependencies(dev_mode: bool, logger: logging.Logger) -> bool:
    """
    Cài đặt các thư viện phụ thuộc
    
    Args:
        dev_mode: True nếu cài đặt môi trường phát triển
        logger: Đối tượng logger
        
    Returns:
        True nếu cài đặt thành công, False nếu không
    """
    requirements_file = "requirements.txt"
    dev_requirements_file = "requirements-dev.txt"
    
    try:
        # Kiểm tra pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                        check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Không tìm thấy pip hoặc pip không hoạt động")
            return False
        
        # Cài đặt các thư viện cơ bản
        if os.path.exists(requirements_file):
            logger.info(f"Đang cài đặt các thư viện từ {requirements_file}...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                    check=True, text=True
                )
                logger.info("Đã cài đặt các thư viện cơ bản")
            except subprocess.CalledProcessError as e:
                logger.error(f"Lỗi khi cài đặt từ {requirements_file}: {e}")
                return False
        else:
            logger.warning(f"Không tìm thấy file {requirements_file}")
            
            # Cài đặt các thư viện thiết yếu
            essential_packages = [
                "requests", "pyyaml", "tqdm", "matplotlib", "pandas", 
                "numpy", "colorama", "rich"
            ]
            logger.info(f"Đang cài đặt các thư viện thiết yếu...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + essential_packages,
                    check=True, text=True
                )
                logger.info("Đã cài đặt các thư viện thiết yếu")
            except subprocess.CalledProcessError as e:
                logger.error(f"Lỗi khi cài đặt thư viện thiết yếu: {e}")
                return False
        
        # Cài đặt các thư viện phát triển (nếu yêu cầu)
        if dev_mode:
            if os.path.exists(dev_requirements_file):
                logger.info(f"Đang cài đặt các thư viện phát triển từ {dev_requirements_file}...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", dev_requirements_file],
                        check=True, text=True
                    )
                    logger.info("Đã cài đặt các thư viện phát triển")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Lỗi khi cài đặt từ {dev_requirements_file}: {e}")
                    return False
            else:
                logger.warning(f"Không tìm thấy file {dev_requirements_file}")
                
                # Cài đặt các thư viện phát triển thiết yếu
                dev_packages = [
                    "pytest", "flake8", "black"
                ]
                logger.info(f"Đang cài đặt các thư viện phát triển thiết yếu...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install"] + dev_packages,
                        check=True, text=True
                    )
                    logger.info("Đã cài đặt các thư viện phát triển thiết yếu")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Lỗi khi cài đặt thư viện phát triển: {e}")
                    return False
        
        logger.info("Đã cài đặt các thư viện phụ thuộc thành công")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi không mong đợi: {e}")
        return False

def create_default_config(config_dir: str, data_dir: str, logs_dir: str,
                         ollama_url: str, force: bool, logger: logging.Logger) -> bool:
    """
    Tạo các file cấu hình mặc định
    
    Args:
        config_dir: Thư mục chứa cấu hình
        data_dir: Thư mục chứa dữ liệu
        logs_dir: Thư mục chứa log
        ollama_url: URL của Ollama API
        force: True nếu ghi đè các file hiện có
        logger: Đối tượng logger
        
    Returns:
        True nếu tạo thành công, False nếu không
    """
    try:
        # 1. Tạo default.yml
        default_config = {
            "system": {
                "version": "1.0.0",
                "log_level": "INFO",
                "log_file": os.path.join(logs_dir, "assistant.log"),
                "data_dir": data_dir,
                "feedback_db": os.path.join(data_dir, "feedback.db"),
                "conversation_dir": os.path.join(data_dir, "conversations"),
                "rlhf_export_dir": os.path.join(data_dir, "rlhf_exports"),
                "config_dir": config_dir
            },
            "ollama": {
                "base_url": ollama_url,
                "timeout": 30,
                "retry_attempts": 3
            },
            "assistant": {
                "default_max_tokens": 1024,
                "default_temperature": 0.7,
                "conversation_history_limit": 100
            },
            "group_discussion": {
                "name": "group_discussion",
                "system_prompt": "Đây là kết quả thảo luận nhóm giữa các AI chuyên gia khác nhau. Mỗi chuyên gia đã đóng góp từ lĩnh vực chuyên môn của họ, và kết quả đã được tổng hợp thành một câu trả lời toàn diện.\n",
                "strengths": {
                    "comprehensive": 0.9,
                    "balanced": 0.88,
                    "thorough": 0.85,
                    "creative": 0.8,
                    "problem_solving": 0.88,
                    "language": 0.85
                },
                "default_rounds": 2
            },
            "optimization": {
                "enabled": True,
                "auto_select_model": True,
                "check_group_discussion_suitability": True,
                "improve_system_prompt": True,
                "improve_user_prompt": True,
                "feedback": {
                    "enabled": True,
                    "collection_probability": 0.3,
                    "collect_comparisons": True,
                    "min_samples_for_update": 5,
                    "feedback_cache_size": 1000,
                    "feedback_collection_methods": ["cli_prompt", "api"],
                    "initial_feedback_boost": True
                },
                "preference": {
                    "weight_update_factor": 0.1,
                    "win_rate_weight": 0.7,
                    "score_weight": 0.3,
                    "default_weight": 1.0,
                    "min_weight": 0.5,
                    "max_weight": 2.0,
                    "periodic_update": True,
                    "update_interval": 10,
                    "smooth_updates": True
                },
                "query_analysis": {
                    "use_cached_categories": True,
                    "category_similarity_threshold": 0.85,
                    "keyword_weighting": True,
                    "complex_query_threshold": 1.8
                },
                "prompt_optimization": {
                    "template_selection_strategy": "best_match",
                    "max_prompt_token_count": 2048,
                    "dynamic_instruction_tuning": True,
                    "instruction_history_window": 20
                },
                "system_prompt_optimization": {
                    "append_only": True,
                    "max_additions": 3,
                    "max_tokens": 512,
                    "instruction_categories": [
                        "performance", "quality", "tone", "format", "domain_specific"
                    ]
                }
            },
            "api": {
                "enabled": False,
                "port": 8000,
                "host": "127.0.0.1",
                "auth_required": True
            }
        }
        
        default_config_path = os.path.join(config_dir, "default.yml")
        if not os.path.exists(default_config_path) or force:
            with open(default_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            logger.info(f"Đã tạo file cấu hình mặc định: {default_config_path}")
        else:
            logger.debug(f"File cấu hình đã tồn tại: {default_config_path}")
        
        # 2. Tạo models.yml
        models_config = {
            "models": [
                {
                    "name": "qwen2.5-coder:7b",
                    "role": "code",
                    "system_prompt": "Bạn là trợ lý lập trình viên chuyên nghiệp.  Nhiệm vụ của bạn là viết mã nguồn chất lượng cao, cung cấp giải pháp  kỹ thuật, debugging và tối ưu hóa code. Hãy tập trung vào các  nguyên tắc clean code, hiệu suất, và bảo mật. Luôn cung cấp giải thích  chi tiết kèm theo mã nguồn.\n",
                    "strengths": {
                        "programming": 0.95,
                        "algorithms": 0.9,
                        "technical_explanation": 0.85,
                        "math": 0.8,
                        "problem_solving": 0.85,
                        "language": 0.75
                    }
                },
                {
                    "name": "deepseek-r1:8b",
                    "role": "deep_thinking",
                    "system_prompt": "Bạn là AI chuyên về tư duy phản biện và phân tích sâu. Hãy xem xét vấn đề từ nhiều góc độ, đánh giá các lập luận, phân tích logic, tìm ra các mâu thuẫn tiềm ẩn, và đưa ra các kết luận có cơ sở. Hãy áp dụng phương pháp tư duy hệ thống và suy nghĩ đa chiều để giải quyết các vấn đề phức tạp.\n",
                    "strengths": {
                        "analysis": 0.95,
                        "critical_thinking": 0.9,
                        "reasoning": 0.92,
                        "evaluation": 0.88,
                        "problem_solving": 0.85,
                        "language": 0.8
                    }
                },
                {
                    "name": "deepseek-r1:1.5b",
                    "role": "llm",
                    "system_prompt": "Bạn là trợ lý AI ngôn ngữ nhỏ gọn, tập trung vào việc trả lời nhanh chóng và hiệu quả. Hãy cung cấp thông tin ngắn gọn, súc tích và đi thẳng vào vấn đề. Ưu tiên độ chính xác và tốc độ. Bạn rất giỏi trong việc tóm tắt thông tin phức tạp thành những điểm chính dễ hiểu.\n",
                    "strengths": {
                        "language": 0.9,
                        "conciseness": 0.95,
                        "clarity": 0.85,
                        "summarization": 0.92,
                        "general_knowledge": 0.75,
                        "communication": 0.88
                    }
                }
            ]
        }
        
        models_config_path = os.path.join(config_dir, "models.yml")
        if not os.path.exists(models_config_path) or force:
            with open(models_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(models_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            logger.info(f"Đã tạo file cấu hình mô hình: {models_config_path}")
        else:
            logger.debug(f"File cấu hình mô hình đã tồn tại: {models_config_path}")
        
        # 3. Tạo prompt_templates.yml
        prompt_templates = {
            "templates": [
                {
                    "name": "general",
                    "description": "Mẫu prompt tổng quát phù hợp cho hầu hết các câu hỏi",
                    "domains": ["general"],
                    "complexity": "medium",
                    "use_cases": ["general", "question", "statement"],
                    "template": "{query}"
                },
                {
                    "name": "programming",
                    "description": "Mẫu prompt cho các câu hỏi lập trình và code",
                    "domains": ["technology", "programming"],
                    "complexity": "high",
                    "use_cases": ["how_to", "code", "technical_explanation"],
                    "template": "Hãy giải quyết vấn đề lập trình sau đây. Cung cấp code đầy đủ, rõ ràng với chú thích chi tiết:\n\n{query}\n\nĐảm bảo code của bạn là:\n- Dễ đọc và tuân theo các nguyên tắc clean code\n- Hiệu quả về mặt thuật toán và tài nguyên\n- Xử lý các trường hợp ngoại lệ và đầu vào không hợp lệ\n- Sử dụng các thực tiễn tốt nhất cho {languages}"
                },
                {
                    "name": "step_by_step",
                    "description": "Mẫu prompt yêu cầu giải thích từng bước",
                    "domains": ["general"],
                    "complexity": "medium",
                    "use_cases": ["how_to", "explanation", "reasoning"],
                    "template": "Hãy giải thích từng bước chi tiết về:\n\n{query}\n\nCung cấp hướng dẫn rõ ràng, tuần tự để tôi có thể hiểu đầy đủ quy trình và logic. Nếu phù hợp, hãy giải thích lý do của từng bước."
                },
                {
                    "name": "creative",
                    "description": "Mẫu prompt cho nội dung sáng tạo",
                    "domains": ["creative", "writing", "arts"],
                    "complexity": "high",
                    "use_cases": ["creative", "writing"],
                    "template": "Hãy sáng tạo nội dung dưới đây với phong cách độc đáo và hấp dẫn:\n\n{query}\n\nHãy sử dụng ngôn ngữ phong phú, tạo hình ảnh sống động, và khai thác các ý tưởng mới mẻ. Đừng ngại phá vỡ các quy ước khi cần thiết để tạo ra tác phẩm thực sự nổi bật."
                }
            ]
        }
        
        templates_path = os.path.join(config_dir, "prompt_templates.yml")
        if not os.path.exists(templates_path) or force:
            with open(templates_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompt_templates, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            logger.info(f"Đã tạo file mẫu prompt: {templates_path}")
        else:
            logger.debug(f"File mẫu prompt đã tồn tại: {templates_path}")
        
        return True
    except Exception as e:
        logger.error(f"Lỗi khi tạo file cấu hình: {e}")
        return False

def setup_dev_environment(logger: logging.Logger) -> bool:
    """
    Thiết lập môi trường phát triển
    
    Args:
        logger: Đối tượng logger
        
    Returns:
        True nếu thiết lập thành công, False nếu không
    """
    try:
        # 1. Tạo file .gitignore nếu chưa có
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# PyCharm
.idea/

# VS Code
.vscode/

# Logs
logs/
*.log

# Data
data/
*.db
*.sqlite3

# Reports
reports/

# Cache
.cache/
.pytest_cache/
.coverage
htmlcov/

# Jupyter
.ipynb_checkpoints
"""
        
        if not os.path.exists(".gitignore"):
            with open(".gitignore", "w", encoding="utf-8") as f:
                f.write(gitignore_content.strip())
            logger.info("Đã tạo file .gitignore")
        else:
            logger.debug("File .gitignore đã tồn tại")
            
        # 2. Tạo file setup.cfg cho flake8, mypy, và pytest
        setup_cfg_content = """
[flake8]
max-line-length = 100
exclude = .git,__pycache__,docs/conf.py,old,build,dist,venv,.venv

[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*
addopts = --verbose
"""
        
        if not os.path.exists("setup.cfg"):
            with open("setup.cfg", "w", encoding="utf-8") as f:
                f.write(setup_cfg_content.strip())
            logger.info("Đã tạo file setup.cfg")
        else:
            logger.debug("File setup.cfg đã tồn tại")
            
        # 3. Tạo file pyproject.toml cho black
        pyproject_content = """
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
        
        if not os.path.exists("pyproject.toml"):
            with open("pyproject.toml", "w", encoding="utf-8") as f:
                f.write(pyproject_content.strip())
            logger.info("Đã tạo file pyproject.toml")
        else:
            logger.debug("File pyproject.toml đã tồn tại")
        
        # 4. Tạo thư mục tests nếu chưa có
        if not os.path.exists("tests"):
            os.makedirs("tests")
            
            # Tạo file __init__.py trong thư mục tests
            with open(os.path.join("tests", "__init__.py"), "w") as f:
                f.write("# Tests package\n")
                
            # Tạo file test mẫu
            test_sample_content = """
import unittest
import sys
import os

# Thêm thư mục gốc vào đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAssistant(unittest.TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def test_sample(self):
        self.assertEqual(1 + 1, 2)
        
if __name__ == '__main__':
    unittest.main()
"""
            
            with open(os.path.join("tests", "test_assistant.py"), "w", encoding="utf-8") as f:
                f.write(test_sample_content.strip())
                
            logger.info("Đã tạo thư mục tests với file test mẫu")
        else:
            logger.debug("Thư mục tests đã tồn tại")
            
        return True
    except Exception as e:
        logger.error(f"Lỗi khi thiết lập môi trường phát triển: {e}")
        return False

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Thiết lập logging
    logger = setup_logging(args.log_level)
    logger.info("Bắt đầu thiết lập hệ thống trợ lý cá nhân...")
    
    # Tạo các thư mục cần thiết
    dirs_to_create = [
        args.config_dir,
        args.data_dir,
        args.logs_dir,
        os.path.join(args.data_dir, "conversations"),
        os.path.join(args.data_dir, "rlhf_exports"),
        os.path.join(args.data_dir, "backups")
    ]
    
    logger.info("Đang tạo các thư mục cần thiết...")
    create_directories(dirs_to_create, logger)
    
    # Cài đặt các thư viện phụ thuộc
    if not args.no_deps:
        logger.info("Đang cài đặt các thư viện phụ thuộc...")
        if not install_dependencies(args.dev, logger):
            logger.warning("Có lỗi khi cài đặt thư viện, tiếp tục thiết lập...")
    else:
        logger.info("Bỏ qua cài đặt thư viện phụ thuộc (--no-deps)")
    
    # Tạo các file cấu hình mặc định
    logger.info("Đang tạo các file cấu hình mặc định...")
    if not create_default_config(
        args.config_dir, args.data_dir, args.logs_dir,
        args.ollama_url, args.force, logger
    ):
        logger.warning("Có lỗi khi tạo file cấu hình, tiếp tục thiết lập...")
    
    # Thiết lập môi trường phát triển nếu yêu cầu
    if args.dev:
        logger.info("Đang thiết lập môi trường phát triển...")
        if not setup_dev_environment(logger):
            logger.warning("Có lỗi khi thiết lập môi trường phát triển")
    
    logger.info("Thiết lập hoàn tất!")
    logger.info(f"- Thư mục cấu hình: {os.path.abspath(args.config_dir)}")
    logger.info(f"- Thư mục dữ liệu: {os.path.abspath(args.data_dir)}")
    logger.info(f"- Thư mục log: {os.path.abspath(args.logs_dir)}")
    logger.info(f"- URL Ollama: {args.ollama_url}")
    
    if not args.no_deps:
        logger.info("Bạn có thể bắt đầu hệ thống bằng lệnh: python main.py --interactive")
    else:
        logger.info("Hãy cài đặt các thư viện phụ thuộc trước khi chạy hệ thống")
        logger.info("pip install -r requirements.txt")

if __name__ == "__main__":
    main()