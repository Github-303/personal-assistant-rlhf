"""
Module cho việc tối ưu hóa câu trả lời dựa trên phân tích truy vấn
"""

import logging
import os
import yaml
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ResponseOptimizer:
    """
    Tối ưu hóa câu trả lời dựa trên phân tích truy vấn người dùng,
    lựa chọn mẫu prompt phù hợp và điều chỉnh hướng dẫn.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo Response Optimizer
        
        Args:
            config: Cấu hình hệ thống
        """
        self.config = config
        self.optimization_config = config.get("optimization", {}).get("prompt_optimization", {})
        
        # Tải các mẫu prompt
        self.prompt_templates = self._load_prompt_templates()
        logger.info(f"Đã tải {len(self.prompt_templates)} mẫu prompt từ {self._get_template_path()}")
        
        # Cấu hình tối ưu
        self.template_selection_strategy = self.optimization_config.get(
            "template_selection_strategy", "best_match")
        self.max_prompt_token_count = self.optimization_config.get(
            "max_prompt_token_count", 2048)
        self.dynamic_instruction_tuning = self.optimization_config.get(
            "dynamic_instruction_tuning", True)
        self.instruction_history_window = self.optimization_config.get(
            "instruction_history_window", 20)
        
        # Bộ nhớ tạm cho các phân tích trước đó
        self.query_analysis_cache = {}
        self.template_performance_history = {}
        
    def _get_template_path(self) -> str:
        """Lấy đường dẫn đến file mẫu prompt"""
        config_dir = self.config.get("system", {}).get("config_dir", "config")
        return os.path.join(config_dir, "prompt_templates.yml")
        
    def _load_prompt_templates(self) -> List[Dict[str, Any]]:
        """Tải các mẫu prompt từ file cấu hình"""
        try:
            template_path = self._get_template_path()
            with open(template_path, 'r', encoding='utf-8') as f:
                templates_data = yaml.safe_load(f)
            return templates_data.get("templates", [])
        except Exception as e:
            logger.error(f"Lỗi khi tải mẫu prompt: {e}")
            return []
    
    def analyze_query(self, query: str, user_info: Optional[Dict] = None, 
                     conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Phân tích truy vấn người dùng để xác định đặc điểm và yêu cầu
        
        Args:
            query: Câu hỏi của người dùng
            user_info: Thông tin về người dùng (tùy chọn)
            conversation_history: Lịch sử hội thoại (tùy chọn)
            
        Returns:
            Dict chứa kết quả phân tích
        """
        # Kiểm tra bộ nhớ cache
        if query in self.query_analysis_cache:
            return self.query_analysis_cache[query].copy()
        
        # Tính độ phức tạp của truy vấn
        complexity_score = self._calculate_complexity(query)
        
        # Xác định lĩnh vực và chủ đề
        domain, topics = self._identify_domain_and_topics(query)
        
        # Xác định kiểu truy vấn
        query_type = self._determine_query_type(query)
        
        # Xác định yêu cầu về định dạng
        format_requirements = self._detect_format_requirements(query)
        
        # Tổng hợp kết quả phân tích
        analysis_result = {
            "complexity": complexity_score,
            "domain": domain,
            "topics": topics,
            "query_type": query_type,
            "format_requirements": format_requirements,
            "requires_code": self._requires_code(query),
            "requires_reasoning": self._requires_reasoning(query),
            "requires_creativity": self._requires_creativity(query),
            "languages": self._detect_languages(query),
            "sentiment": self._analyze_sentiment(query),
            "urgency": self._detect_urgency(query)
        }
        
        # Lưu vào bộ nhớ cache
        self.query_analysis_cache[query] = analysis_result.copy()
        
        return analysis_result
    
    def optimize_query(self, query: str, user_info: Optional[Dict] = None,
                      conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Tối ưu hóa truy vấn dựa trên phân tích
        
        Args:
            query: Câu hỏi của người dùng
            user_info: Thông tin về người dùng (tùy chọn)
            conversation_history: Lịch sử hội thoại (tùy chọn)
            
        Returns:
            Dict chứa kết quả phân tích và prompt đã được tối ưu
        """
        try:
            # Phân tích truy vấn
            analysis = self.analyze_query(query, user_info, conversation_history)
            
            # Lựa chọn mẫu prompt phù hợp
            selected_template = self._select_best_template(analysis)
            
            # Tối ưu prompt dựa trên phân tích
            optimized_prompt = self._optimize_prompt_from_template(
                query, analysis, selected_template)
            
            return {
                "analysis": analysis,
                "template_used": selected_template.get("name", "default"),
                "optimized_prompt": optimized_prompt
            }
        except Exception as e:
            logger.error(f"Lỗi khi tối ưu hóa truy vấn: {e}")
            return {
                "analysis": {},
                "template_used": "default",
                "optimized_prompt": query
            }
    
    # Thêm phương thức alias để tương thích với mã gọi hiện tại
    def optimize_query_result(self, query: str, user_info: Optional[Dict] = None,
                            conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Alias cho phương thức optimize_query để đảm bảo tương thích
        với mã hiện tại đang gọi phương thức này
        """
        return self.optimize_query(query, user_info, conversation_history)
            
    def _calculate_complexity(self, query: str) -> float:
        """Tính toán độ phức tạp của truy vấn"""
        # Xem xét các yếu tố như độ dài, cấu trúc câu, từ khóa phức tạp
        complexity = min(5.0, (len(query) / 100) + 
                        (query.count(',') * 0.1) + 
                        (query.count('?') * 0.3))
        
        # Kiểm tra từ khóa chỉ báo độ phức tạp
        complex_indicators = [
            "tại sao", "giải thích", "phân tích", "so sánh", "đánh giá",
            "nguyên nhân", "hậu quả", "tác động", "chiến lược", "giải pháp toàn diện"
        ]
        
        for indicator in complex_indicators:
            if indicator in query.lower():
                complexity += 0.5
                
        return min(10.0, complexity)
    
    def _identify_domain_and_topics(self, query: str) -> Tuple[str, List[str]]:
        """Xác định lĩnh vực và chủ đề của truy vấn"""
        # Phân loại lĩnh vực dựa trên từ khóa
        domains = {
            "technology": ["máy tính", "phần mềm", "công nghệ", "lập trình", "code", "AI", "ứng dụng"],
            "business": ["kinh doanh", "marketing", "tài chính", "quản lý", "chiến lược", "đầu tư"],
            "science": ["khoa học", "vật lý", "hóa học", "sinh học", "toán học", "nghiên cứu"],
            "health": ["sức khỏe", "y tế", "bệnh", "thuốc", "điều trị", "dinh dưỡng"],
            "education": ["giáo dục", "học tập", "trường học", "đại học", "kiến thức", "dạy"],
            "arts": ["nghệ thuật", "âm nhạc", "phim", "văn học", "thiết kế", "sáng tạo"],
            "lifestyle": ["lối sống", "du lịch", "ẩm thực", "thời trang", "thể thao"]
        }
        
        # Đếm số từ khóa khớp cho mỗi lĩnh vực
        domain_scores = {domain: 0 for domain in domains}
        detected_topics = []
        
        query_lower = query.lower()
        for domain, keywords in domains.items():
            for keyword in keywords:
                if keyword in query_lower:
                    domain_scores[domain] += 1
                    if keyword not in detected_topics:
                        detected_topics.append(keyword)
        
        # Chọn lĩnh vực có điểm cao nhất
        main_domain = max(domain_scores, key=domain_scores.get)
        if domain_scores[main_domain] == 0:
            main_domain = "general"
            
        return main_domain, detected_topics
    
    def _determine_query_type(self, query: str) -> str:
        """Xác định loại truy vấn"""
        query_lower = query.lower()
        
        if any(q in query_lower for q in ["làm thế nào", "làm sao", "cách"]):
            return "how_to"
        elif any(q in query_lower for q in ["tại sao", "vì sao", "lý do"]):
            return "why"
        elif any(q in query_lower for q in ["là gì", "định nghĩa", "giải thích"]):
            return "what_is"
        elif any(q in query_lower for q in ["so sánh", "khác nhau", "giống nhau"]):
            return "comparison"
        elif any(q in query_lower for q in ["ví dụ", "minh họa"]):
            return "example"
        elif any(q in query_lower for q in ["liệt kê", "danh sách", "các loại"]):
            return "list"
        elif any(q in query_lower for q in ["đánh giá", "nhận xét", "ý kiến"]):
            return "opinion"
        elif any(q in query_lower for q in ["dự đoán", "tương lai", "sẽ"]):
            return "prediction"
        elif "?" in query:
            return "question"
        else:
            return "statement"
    
    def _detect_format_requirements(self, query: str) -> Dict[str, bool]:
        """Phát hiện yêu cầu về định dạng từ truy vấn"""
        query_lower = query.lower()
        
        return {
            "requires_list": any(kw in query_lower for kw in ["liệt kê", "danh sách", "các điểm"]),
            "requires_step_by_step": any(kw in query_lower for kw in ["từng bước", "chi tiết", "hướng dẫn"]),
            "requires_examples": any(kw in query_lower for kw in ["ví dụ", "minh họa", "mẫu"]),
            "requires_summary": any(kw in query_lower for kw in ["tóm tắt", "tổng hợp", "tóm lược"]),
            "requires_comparison": any(kw in query_lower for kw in ["so sánh", "đối chiếu", "khác biệt"]),
            "requires_pros_cons": any(kw in query_lower for kw in ["ưu điểm", "nhược điểm", "lợi ích", "hạn chế"]),
            "requires_table": any(kw in query_lower for kw in ["bảng", "biểu"]),
            "requires_diagram": any(kw in query_lower for kw in ["sơ đồ", "biểu đồ", "hình vẽ"])
        }
    
    def _requires_code(self, query: str) -> bool:
        """Kiểm tra xem truy vấn có yêu cầu code hay không"""
        code_indicators = [
            "code", "mã", "lập trình", "function", "hàm", "class", "implement",
            "algorithm", "thuật toán", "script", "module", "debug", "fix", "sửa lỗi"
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in code_indicators)
    
    def _requires_reasoning(self, query: str) -> bool:
        """Kiểm tra xem truy vấn có đòi hỏi suy luận hay không"""
        reasoning_indicators = [
            "tại sao", "vì sao", "lý do", "giải thích", "phân tích",
            "đánh giá", "nhận định", "suy luận", "kết luận", "hệ quả"
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in reasoning_indicators)
    
    def _requires_creativity(self, query: str) -> bool:
        """Kiểm tra xem truy vấn có đòi hỏi sáng tạo hay không"""
        creativity_indicators = [
            "sáng tạo", "ý tưởng", "thiết kế", "tưởng tượng", "viết",
            "sáng tác", "kể chuyện", "hư cấu", "nghệ thuật", "độc đáo"
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in creativity_indicators)
    
    def _detect_languages(self, query: str) -> List[str]:
        """Phát hiện ngôn ngữ được sử dụng trong truy vấn"""
        # Đơn giản hóa: chỉ phát hiện tiếng Việt và tiếng Anh
        vietnamese_chars = "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
        
        if any(c in vietnamese_chars for c in query.lower()):
            return ["vietnamese"]
        elif query.isascii():
            return ["english"]
        else:
            return ["vietnamese", "english"]
    
    def _analyze_sentiment(self, query: str) -> str:
        """Phân tích cảm xúc trong truy vấn"""
        positive_words = ["tốt", "hay", "tuyệt", "thích", "vui", "hạnh phúc", "hài lòng"]
        negative_words = ["tệ", "kém", "buồn", "thất vọng", "khó chịu", "không thích"]
        query_lower = query.lower()
        
        positive_count = sum(1 for word in positive_words if word in query_lower)
        negative_count = sum(1 for word in negative_words if word in query_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _detect_urgency(self, query: str) -> str:
        """Phát hiện mức độ khẩn cấp trong truy vấn"""
        urgent_indicators = ["khẩn cấp", "gấp", "ngay", "nhanh", "sớm", "càng sớm càng tốt"]
        query_lower = query.lower()
        
        if any(indicator in query_lower for indicator in urgent_indicators):
            return "high"
        else:
            return "normal"
    
    def _select_best_template(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lựa chọn mẫu prompt phù hợp nhất dựa trên kết quả phân tích
        
        Args:
            analysis: Kết quả phân tích truy vấn
            
        Returns:
            Mẫu prompt được chọn
        """
        if not self.prompt_templates:
            # Trả về mẫu mặc định nếu không có mẫu nào
            return {
                "name": "default",
                "description": "Mẫu mặc định",
                "template": "{query}",
                "use_cases": ["general"]
            }
        
        # Chiến lược lựa chọn
        if self.template_selection_strategy == "best_match":
            return self._select_best_match_template(analysis)
        elif self.template_selection_strategy == "performance_based":
            return self._select_performance_based_template(analysis)
        else:
            # Mặc định sử dụng best_match
            return self._select_best_match_template(analysis)
    
    def _select_best_match_template(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Chọn mẫu phù hợp nhất dựa trên đối sánh với phân tích"""
        scores = []
        
        for template in self.prompt_templates:
            score = 0
            
            # Điểm cho lĩnh vực phù hợp
            if analysis.get("domain") in template.get("domains", []):
                score += 3
            elif "general" in template.get("domains", []):
                score += 1
                
            # Điểm cho trường hợp sử dụng
            for use_case in template.get("use_cases", []):
                if use_case == analysis.get("query_type"):
                    score += 2
                if use_case == "code" and analysis.get("requires_code"):
                    score += 2
                if use_case == "reasoning" and analysis.get("requires_reasoning"):
                    score += 2
                if use_case == "creative" and analysis.get("requires_creativity"):
                    score += 2
                    
            # Điểm cho độ phức tạp
            template_complexity = template.get("complexity", "medium")
            if (template_complexity == "high" and analysis.get("complexity", 0) > 7) or \
               (template_complexity == "medium" and 3 <= analysis.get("complexity", 0) <= 7) or \
               (template_complexity == "low" and analysis.get("complexity", 0) < 3):
                score += 2
                
            scores.append((template, score))
            
        # Chọn mẫu có điểm cao nhất
        if scores:
            best_template = max(scores, key=lambda x: x[1])[0]
            return best_template
        
        # Trả về mẫu mặc định nếu không có điểm nào
        return self.prompt_templates[0] if self.prompt_templates else {
            "name": "default",
            "template": "{query}"
        }
    
    def _select_performance_based_template(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Chọn mẫu dựa trên hiệu suất trong quá khứ"""
        # Lọc các mẫu phù hợp với phân tích
        matching_templates = []
        for template in self.prompt_templates:
            if (analysis.get("domain") in template.get("domains", []) or
                "general" in template.get("domains", [])):
                matching_templates.append(template)
                
        if not matching_templates:
            matching_templates = self.prompt_templates
            
        # Sắp xếp theo hiệu suất trong quá khứ
        templates_with_scores = []
        for template in matching_templates:
            template_name = template.get("name")
            performance_score = self.template_performance_history.get(template_name, {}).get("score", 0.5)
            templates_with_scores.append((template, performance_score))
            
        # Chọn mẫu có điểm hiệu suất cao nhất
        if templates_with_scores:
            best_template = max(templates_with_scores, key=lambda x: x[1])[0]
            return best_template
            
        # Trả về mẫu mặc định nếu không có điểm nào
        return matching_templates[0] if matching_templates else {
            "name": "default",
            "template": "{query}"
        }
    
    def _optimize_prompt_from_template(self, query: str, analysis: Dict[str, Any], 
                                     template: Dict[str, Any]) -> str:
        """
        Tối ưu hóa prompt dựa trên mẫu đã chọn và kết quả phân tích
        
        Args:
            query: Truy vấn gốc
            analysis: Kết quả phân tích
            template: Mẫu prompt đã chọn
            
        Returns:
            Prompt đã được tối ưu hóa
        """
        # Lấy mẫu prompt
        prompt_template = template.get("template", "{query}")
        
        # Các thay thế cơ bản
        replacements = {
            "{query}": query,
            "{domain}": analysis.get("domain", "general"),
            "{complexity}": str(analysis.get("complexity", 0)),
            "{query_type}": analysis.get("query_type", "general"),
            "{topics}": ", ".join(analysis.get("topics", [])),
            "{requires_code}": "true" if analysis.get("requires_code") else "false",
            "{requires_reasoning}": "true" if analysis.get("requires_reasoning") else "false",
            "{requires_creativity}": "true" if analysis.get("requires_creativity") else "false",
            "{format_requirements}": self._format_requirements_to_string(analysis.get("format_requirements", {})),
            "{sentiment}": analysis.get("sentiment", "neutral"),
            "{urgency}": analysis.get("urgency", "normal"),
            "{languages}": ", ".join(analysis.get("languages", ["vietnamese"])),
        }
        
        # Thực hiện các thay thế
        optimized_prompt = prompt_template
        for key, value in replacements.items():
            optimized_prompt = optimized_prompt.replace(key, value)
            
        # Thêm hướng dẫn bổ sung nếu cần
        if self.dynamic_instruction_tuning:
            additional_instructions = self._generate_additional_instructions(analysis)
            if additional_instructions:
                optimized_prompt += f"\n\n{additional_instructions}"
                
        return optimized_prompt
    
    def _format_requirements_to_string(self, format_reqs: Dict[str, bool]) -> str:
        """Chuyển đổi yêu cầu định dạng thành chuỗi hướng dẫn"""
        instructions = []
        
        for req, value in format_reqs.items():
            if value:
                if req == "requires_list":
                    instructions.append("Trình bày kết quả dưới dạng danh sách có cấu trúc.")
                elif req == "requires_step_by_step":
                    instructions.append("Cung cấp hướng dẫn từng bước chi tiết.")
                elif req == "requires_examples":
                    instructions.append("Đưa ra các ví dụ cụ thể để minh họa.")
                elif req == "requires_summary":
                    instructions.append("Kèm theo tóm tắt ngắn gọn các điểm chính.")
                elif req == "requires_comparison":
                    instructions.append("So sánh rõ ràng các khía cạnh khác nhau.")
                elif req == "requires_pros_cons":
                    instructions.append("Liệt kê ưu điểm và nhược điểm.")
                elif req == "requires_table":
                    instructions.append("Trình bày dữ liệu dưới dạng bảng nếu phù hợp.")
                elif req == "requires_diagram":
                    instructions.append("Mô tả bằng sơ đồ hoặc biểu đồ nếu có thể.")
                    
        return " ".join(instructions)
    
    def _generate_additional_instructions(self, analysis: Dict[str, Any]) -> str:
        """Tạo hướng dẫn bổ sung dựa trên phân tích"""
        instructions = []
        
        # Thêm hướng dẫn dựa trên độ phức tạp
        if analysis.get("complexity", 0) > 7:
            instructions.append("Phân tích vấn đề một cách toàn diện, xem xét nhiều khía cạnh và cung cấp phân tích sâu.")
        elif analysis.get("complexity", 0) < 3:
            instructions.append("Cung cấp câu trả lời ngắn gọn, súc tích và dễ hiểu.")
            
        # Thêm hướng dẫn dựa trên yêu cầu
        if analysis.get("requires_code"):
            instructions.append("Đưa ra mã nguồn rõ ràng, có chú thích và tuân thủ các nguyên tắc clean code.")
            
        if analysis.get("requires_reasoning"):
            instructions.append("Giải thích logic và lý luận chi tiết, đưa ra các luận điểm có cơ sở.")
            
        if analysis.get("requires_creativity"):
            instructions.append("Thể hiện sự sáng tạo, độc đáo và tư duy ngoài khuôn khổ.")
            
        # Thêm hướng dẫn dựa trên ngôn ngữ
        if "vietnamese" in analysis.get("languages", []):
            instructions.append("Trả lời bằng tiếng Việt, sử dụng các thuật ngữ phù hợp với văn phong tự nhiên.")
            
        # Thêm hướng dẫn dựa trên mức độ khẩn cấp
        if analysis.get("urgency") == "high":
            instructions.append("Ưu tiên cung cấp thông tin thiết yếu và giải pháp nhanh chóng.")
            
        return " ".join(instructions)
    
    def update_template_performance(self, template_name: str, feedback_score: float) -> None:
        """
        Cập nhật hiệu suất của mẫu dựa trên phản hồi
        
        Args:
            template_name: Tên của mẫu
            feedback_score: Điểm phản hồi (0-1)
        """
        if template_name not in self.template_performance_history:
            self.template_performance_history[template_name] = {
                "score": 0.5,
                "count": 0
            }
            
        current = self.template_performance_history[template_name]
        current_count = current["count"]
        current_score = current["score"]
        
        # Cập nhật điểm với trọng số giảm dần
        updated_score = (current_score * current_count + feedback_score) / (current_count + 1)
        
        self.template_performance_history[template_name] = {
            "score": updated_score,
            "count": current_count + 1
        }
        
    def clear_cache(self) -> None:
        """Xóa bộ nhớ cache"""
        self.query_analysis_cache.clear()