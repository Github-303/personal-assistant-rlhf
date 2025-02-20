"""
Quản lý các mẫu prompt cho hệ thống.
Cung cấp các tiện ích để tải, tùy chỉnh và sử dụng mẫu prompt.
"""

import os
import yaml
import logging
import re
from typing import Dict, Any, Optional, List, Union
from string import Template

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Lớp quản lý và tùy chỉnh các mẫu prompt."""
    
    def __init__(self, template_str: str):
        """
        Khởi tạo mẫu prompt.
        
        Args:
            template_str: Chuỗi mẫu
        """
        self.template_str = template_str
        self.template = Template(template_str)
    
    def format(self, **kwargs) -> str:
        """
        Định dạng mẫu với các tham số.
        
        Args:
            **kwargs: Tham số để thay thế trong mẫu
            
        Returns:
            Chuỗi đã định dạng
        """
        try:
            return self.template.substitute(**kwargs)
        except KeyError as e:
            logger.warning(f"Thiếu tham số {e} khi định dạng mẫu prompt")
            # Sử dụng safe_substitute để tránh lỗi khi thiếu tham số
            return self.template.safe_substitute(**kwargs)
    
    def __str__(self) -> str:
        """Lấy chuỗi mẫu."""
        return self.template_str


class PromptLibrary:
    """Thư viện quản lý các mẫu prompt."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo thư viện mẫu prompt.
        
        Args:
            config: Cấu hình hệ thống
        """
        self.config = config
        self.templates = {}
        self.load_templates()
    
    def load_templates(self) -> None:
        """Tải các mẫu prompt từ file cấu hình."""
        config_dir = self.config.get("system", {}).get("config_dir", "config")
        template_path = os.path.join(config_dir, "prompt_templates.yml")
        
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    templates_config = yaml.safe_load(f)
                    
                if templates_config and isinstance(templates_config, dict):
                    for role, role_templates in templates_config.items():
                        if isinstance(role_templates, dict):
                            self.templates[role] = {}
                            for template_name, template_str in role_templates.items():
                                if isinstance(template_str, str):
                                    self.templates[role][template_name] = PromptTemplate(template_str)
                                    
                    logger.info(f"Đã tải {self._count_templates()} mẫu prompt từ {template_path}")
                else:
                    logger.warning(f"File mẫu prompt không đúng định dạng: {template_path}")
                    self._load_default_templates()
            except Exception as e:
                logger.error(f"Lỗi khi tải mẫu prompt từ {template_path}: {e}")
                self._load_default_templates()
        else:
            logger.warning(f"Không tìm thấy file mẫu prompt: {template_path}")
            self._load_default_templates()
    
    def _count_templates(self) -> int:
        """
        Đếm tổng số mẫu prompt đã tải.
        
        Returns:
            Số lượng mẫu
        """
        count = 0
        for role, templates in self.templates.items():
            count += len(templates)
        return count
    
    def _load_default_templates(self) -> None:
        """Tải các mẫu prompt mặc định."""
        self.templates = {
            "code": {
                "default": PromptTemplate(
                    "Hãy cung cấp một câu trả lời chi tiết, kỹ thuật và chính xác về vấn đề sau:\n${query}\n\n"
                    "Trong câu trả lời của bạn, hãy bao gồm:\n"
                    "1. Giải thích kỹ thuật chi tiết\n"
                    "2. Ví dụ cụ thể và mã nguồn (nếu thích hợp)\n"
                    "3. Các phương pháp tiếp cận thay thế\n"
                    "4. Cân nhắc về hiệu suất và bảo mật\n"
                    "5. Tài liệu tham khảo hoặc nguồn (nếu thích hợp)"
                )
            },
            "deep_thinking": {
                "default": PromptTemplate(
                    "Hãy suy ngẫm sâu sắc về câu hỏi sau đây, đánh giá nó từ nhiều khía cạnh và đưa ra "
                    "một phản hồi cân bằng, đầy đủ và thấu đáo:\n${query}\n\n"
                    "Trong câu trả lời của bạn, hãy:\n"
                    "1. Cung cấp phân tích nhiều chiều\n"
                    "2. Xem xét các mâu thuẫn và nghịch lý\n"
                    "3. Kết nối với ngữ cảnh rộng hơn\n"
                    "4. Xem xét các hệ quả ngắn hạn và dài hạn\n"
                    "5. Đưa ra kết luận có chiều sâu và cân nhắc"
                )
            },
            "llm": {
                "default": PromptTemplate(
                    "Hãy cung cấp một câu trả lời ngắn gọn, rõ ràng và hiệu quả cho:\n${query}\n\n"
                    "Câu trả lời nên:\n"
                    "1. Đi thẳng vào vấn đề\n"
                    "2. Sử dụng ngôn ngữ đơn giản và dễ hiểu\n"
                    "3. Tập trung vào thông tin thiết yếu\n"
                    "4. Có cấu trúc rõ ràng\n"
                    "5. Dễ dàng tiếp thu"
                )
            },
            "group_discussion": {
                "default": PromptTemplate(
                    "Hãy suy nghĩ kỹ về vấn đề sau đây từ nhiều góc độ, xem xét các khía cạnh kỹ thuật, "
                    "phân tích sâu và trình bày rõ ràng:\n${query}\n\n"
                    "Trong câu trả lời của bạn, hãy:\n"
                    "1. Cung cấp cả thông tin kỹ thuật và phân tích sâu sắc\n"
                    "2. Xem xét các góc nhìn khác nhau\n"
                    "3. Đề xuất giải pháp thực tế và có cơ sở\n"
                    "4. Cân bằng giữa chi tiết kỹ thuật và khả năng tiếp cận\n"
                    "5. Tổng hợp thành một câu trả lời toàn diện và mạch lạc"
                )
            }
        }
        logger.info(f"Đã tải {self._count_templates()} mẫu prompt mặc định")
    
    def get_template(self, role: str, template_name: str = "default") -> Optional[PromptTemplate]:
        """
        Lấy mẫu prompt theo vai trò và tên.
        
        Args:
            role: Vai trò của mô hình
            template_name: Tên mẫu
            
        Returns:
            Đối tượng PromptTemplate hoặc None nếu không tìm thấy
        """
        if role in self.templates and template_name in self.templates[role]:
            return self.templates[role][template_name]
        
        # Fallback về mẫu mặc định nếu không tìm thấy mẫu cụ thể
        if role in self.templates and "default" in self.templates[role]:
            logger.debug(f"Không tìm thấy mẫu '{template_name}' cho vai trò '{role}', sử dụng mẫu mặc định")
            return self.templates[role]["default"]
            
        logger.warning(f"Không tìm thấy mẫu nào cho vai trò '{role}'")
        return None
    
    def format_prompt(self, role: str, template_name: str = "default", **kwargs) -> str:
        """
        Định dạng prompt với tham số đã cho.
        
        Args:
            role: Vai trò của mô hình
            template_name: Tên mẫu
            **kwargs: Các tham số để thay thế
            
        Returns:
            Chuỗi đã định dạng hoặc trả về query gốc nếu không tìm thấy mẫu
        """
        template = self.get_template(role, template_name)
        
        if template:
            return template.format(**kwargs)
        
        # Nếu không tìm thấy mẫu, trả về query gốc
        if "query" in kwargs:
            logger.warning(f"Không tìm thấy mẫu nào phù hợp, trả về query gốc")
            return kwargs["query"]
            
        # Không có gì để trả về
        logger.error("Không thể định dạng prompt: không tìm thấy mẫu và không có query")
        return ""
    
    def get_system_prompt(self, role: str) -> str:
        """
        Lấy system prompt cho vai trò chỉ định.
        
        Args:
            role: Vai trò của mô hình
        
        Returns:
            System prompt
        """
        models_config = self.config.get("models", [])
        
        for model_config in models_config:
            if model_config.get("role") == role:
                return model_config.get("system_prompt", "")
        
        # Fallback về system prompt mặc định nếu không tìm thấy
        if role == "code":
            return "Bạn là trợ lý lập trình viên chuyên nghiệp. Nhiệm vụ của bạn là viết mã nguồn chất lượng cao."
        elif role == "deep_thinking":
            return "Bạn là AI chuyên về tư duy phản biện và phân tích sâu."
        elif role == "llm":
            return "Bạn là trợ lý AI ngôn ngữ nhỏ gọn, tập trung vào việc trả lời nhanh chóng và hiệu quả."
        elif role == "group_discussion":
            return "Bạn là trợ lý tổng hợp thông tin, có nhiệm vụ tạo ra phản hồi cuối cùng dựa trên thảo luận nhóm."
            
        return ""

def load_prompt_library(config: Dict[str, Any]) -> PromptLibrary:
    """
    Tải thư viện mẫu prompt.
    
    Args:
        config: Cấu hình hệ thống
        
    Returns:
        Đối tượng PromptLibrary
    """
    return PromptLibrary(config)
