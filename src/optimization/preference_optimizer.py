"""
Module tối ưu hóa sở thích mô hình dựa trên phân tích điểm mạnh và phản hồi
"""

import logging
import json
import random
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Set

logger = logging.getLogger(__name__)

class PreferenceOptimizer:
    """
    Tối ưu hóa sở thích mô hình dựa trên:
    - Điểm mạnh của mô hình (strengths)
    - Phản hồi của người dùng (RLHF/DPO)
    - Phân tích truy vấn và yêu cầu
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo Preference Optimizer
        
        Args:
            config: Cấu hình hệ thống
        """
        self.config = config
        self.preference_config = config.get("optimization", {}).get("preference", {})
        self.models_config = config.get("models", [])
        
        # Khai báo điểm mạnh mặc định
        self.strength_categories = [
            "programming", "analysis", "creative", "reasoning", 
            "math", "language", "technical_explanation", "evaluation",
            "critical_thinking", "problem_solving", "algorithms",
            "conciseness", "clarity", "summarization", "general_knowledge",
            "communication", "balanced", "comprehensive", "thorough"
        ]
        
        # Tải điểm mạnh của mô hình
        self.model_strengths = self._load_model_strengths()
        logger.info(f"Đã khởi tạo điểm mạnh cho {len(self.model_strengths)} mô hình")
        
        # Cấu hình trọng số
        self.weight_update_factor = self.preference_config.get("weight_update_factor", 0.1)
        self.win_rate_weight = self.preference_config.get("win_rate_weight", 0.7)
        self.score_weight = self.preference_config.get("score_weight", 0.3)
        self.default_weight = self.preference_config.get("default_weight", 1.0)
        self.min_weight = self.preference_config.get("min_weight", 0.5)
        self.max_weight = self.preference_config.get("max_weight", 2.0)
        
        # Theo dõi số lần chọn và điểm số
        self.model_selection_count = {}
        self.model_win_rate = {}
        self.model_avg_score = {}
        self.model_weights = {}
        
        # Cache cho hiệu suất mô hình theo loại truy vấn
        self.model_performance_cache = {}
        
        # Khởi tạo trọng số mặc định
        self._initialize_weights()
        
    def _load_model_strengths(self) -> Dict[str, Dict[str, float]]:
        """
        Tải điểm mạnh của mô hình từ cấu hình
        
        Returns:
            Dict chứa điểm mạnh của mỗi mô hình
        """
        model_strengths = {}
        
        # Lấy điểm mạnh từ cấu hình
        for model_config in self.models_config:
            model_name = model_config.get("name")
            if not model_name:
                continue
                
            strengths = model_config.get("strengths", {})
            
            # Đảm bảo các danh mục điểm mạnh chuẩn hóa
            normalized_strengths = {}
            for category in self.strength_categories:
                normalized_strengths[category] = strengths.get(category, 0.5)
                
            model_strengths[model_name] = normalized_strengths
            
        # Thêm thảo luận nhóm nếu có
        group_discussion = self.config.get("group_discussion", {})
        if group_discussion and "name" in group_discussion:
            group_name = group_discussion.get("name", "group_discussion")
            group_strengths = group_discussion.get("strengths", {})
            
            normalized_strengths = {}
            for category in self.strength_categories:
                normalized_strengths[category] = group_strengths.get(category, 0.7)
                
            model_strengths[group_name] = normalized_strengths
            
        return model_strengths
    
    def _initialize_weights(self) -> None:
        """Khởi tạo trọng số mặc định cho mỗi mô hình"""
        for model_name in self.model_strengths.keys():
            self.model_weights[model_name] = self.default_weight
            self.model_selection_count[model_name] = 0
            self.model_win_rate[model_name] = 0.5  # Tỷ lệ thắng mặc định là 50%
            self.model_avg_score[model_name] = 0.5  # Điểm trung bình mặc định là 0.5
    
    def select_best_model(self, query_analysis: Dict[str, Any], 
                         available_models: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Chọn mô hình tốt nhất dựa trên phân tích truy vấn và điểm mạnh
        
        Args:
            query_analysis: Kết quả phân tích truy vấn
            available_models: Danh sách mô hình khả dụng (tùy chọn)
            
        Returns:
            Tên của mô hình được chọn hoặc None
        """
        # Kiểm tra nếu không có mô hình khả dụng
        if not available_models and not self.model_strengths:
            return None
            
        # Lấy danh sách mô hình từ tham số hoặc cấu hình
        model_list = []
        if available_models:
            model_list = available_models
        else:
            model_list = self.models_config
            
        # Danh sách tên mô hình
        model_names = [model.get("name") for model in model_list if model.get("name")]
        model_names = [name for name in model_names if name in self.model_strengths]
        
        if not model_names:
            return None
            
        # Xác định điểm mạnh cần thiết từ phân tích truy vấn
        required_strengths = self._determine_required_strengths(query_analysis)
        
        # Tính điểm cho mỗi mô hình
        model_scores = {}
        for model_name in model_names:
            strengths = self.model_strengths.get(model_name, {})
            score = self._calculate_model_score(strengths, required_strengths)
            
            # Điều chỉnh điểm dựa trên trọng số
            weight = self.model_weights.get(model_name, self.default_weight)
            adjusted_score = score * weight
            
            model_scores[model_name] = adjusted_score
            
        # Chọn mô hình có điểm cao nhất
        if model_scores:
            best_model = max(model_scores.items(), key=lambda x: x[1])[0]
            
            # Cập nhật số lần chọn
            self.model_selection_count[best_model] = self.model_selection_count.get(best_model, 0) + 1
            
            return best_model
            
        # Mặc định chọn mô hình đầu tiên nếu không tính được điểm
        return model_names[0] if model_names else None
    
    def update_weights_from_feedback(self, query: str, responses: Dict[str, str],
                                    selected_response: str, feedback_score: Optional[float] = None) -> None:
        """
        Cập nhật trọng số dựa trên phản hồi người dùng
        
        Args:
            query: Truy vấn người dùng
            responses: Dict các câu trả lời với key là model_name
            selected_response: Tên mô hình được chọn
            feedback_score: Điểm đánh giá (0-1, tùy chọn)
        """
        if not selected_response or selected_response not in self.model_weights:
            return
            
        # Cập nhật tỷ lệ thắng
        participating_models = list(responses.keys())
        if len(participating_models) > 1 and selected_response in participating_models:
            for model in participating_models:
                if model == selected_response:
                    self._update_win_rate(model, True)
                else:
                    self._update_win_rate(model, False)
                    
        # Cập nhật điểm trung bình
        if feedback_score is not None:
            current_avg = self.model_avg_score.get(selected_response, 0.5)
            count = self.model_selection_count.get(selected_response, 1)
            # Trung bình có trọng số, ưu tiên giá trị mới hơn
            new_avg = (current_avg * 0.9 * count + feedback_score * 0.1 * count) / count
            self.model_avg_score[selected_response] = new_avg
            
        # Cập nhật trọng số
        win_rate = self.model_win_rate.get(selected_response, 0.5)
        avg_score = self.model_avg_score.get(selected_response, 0.5)
        
        # Tính toán trọng số mới dựa trên tỷ lệ thắng và điểm trung bình
        performance_score = (
            win_rate * self.win_rate_weight +
            avg_score * self.score_weight
        )
        
        # Điều chỉnh trọng số
        current_weight = self.model_weights.get(selected_response, self.default_weight)
        adjustment = (performance_score - 0.5) * self.weight_update_factor
        
        new_weight = current_weight + adjustment
        new_weight = max(self.min_weight, min(self.max_weight, new_weight))
        
        self.model_weights[selected_response] = new_weight
        
        # Cập nhật cache hiệu suất
        self._update_performance_cache(query, selected_response, feedback_score)
    
    def _update_win_rate(self, model_name: str, is_win: bool) -> None:
        """
        Cập nhật tỷ lệ thắng của mô hình
        
        Args:
            model_name: Tên mô hình
            is_win: True nếu mô hình được chọn, False nếu không
        """
        if model_name not in self.model_win_rate:
            self.model_win_rate[model_name] = 0.5
            self.model_selection_count[model_name] = 0
            
        current_rate = self.model_win_rate[model_name]
        count = self.model_selection_count[model_name]
        new_count = count + 1
        
        # Tỷ lệ thắng mới với trọng số giảm dần theo thời gian
        decay_factor = min(100, new_count) / (min(100, new_count) + 10)
        win_value = 1.0 if is_win else 0.0
        
        new_rate = current_rate * decay_factor + win_value * (1 - decay_factor)
        
        self.model_win_rate[model_name] = new_rate
        self.model_selection_count[model_name] = new_count
    
    def _determine_required_strengths(self, query_analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Xác định điểm mạnh cần thiết dựa trên phân tích truy vấn
        
        Args:
            query_analysis: Kết quả phân tích truy vấn
            
        Returns:
            Dict chứa điểm mạnh cần thiết và mức độ ưu tiên
        """
        required_strengths = {}
        
        # Mặc định mỗi điểm mạnh có mức ưu tiên thấp
        for category in self.strength_categories:
            required_strengths[category] = 0.1
            
        # Dựa vào phân tích, điều chỉnh mức ưu tiên
        if query_analysis.get("requires_code", False):
            required_strengths["programming"] = 0.9
            required_strengths["algorithms"] = 0.7
            required_strengths["technical_explanation"] = 0.6
            
        if query_analysis.get("requires_reasoning", False):
            required_strengths["reasoning"] = 0.8
            required_strengths["critical_thinking"] = 0.7
            required_strengths["analysis"] = 0.7
            required_strengths["evaluation"] = 0.6
            
        if query_analysis.get("requires_creativity", False):
            required_strengths["creative"] = 0.9
            
        # Dựa vào độ phức tạp
        complexity = query_analysis.get("complexity", 0)
        if complexity > 7:
            required_strengths["comprehensive"] = 0.8
            required_strengths["thorough"] = 0.7
            required_strengths["balanced"] = 0.6
        elif complexity < 3:
            required_strengths["conciseness"] = 0.8
            required_strengths["clarity"] = 0.7
            
        # Dựa vào loại truy vấn
        query_type = query_analysis.get("query_type", "")
        if query_type == "how_to":
            required_strengths["technical_explanation"] = 0.7
            required_strengths["clarity"] = 0.7
        elif query_type == "comparison":
            required_strengths["balanced"] = 0.8
            required_strengths["analysis"] = 0.7
        elif query_type == "what_is":
            required_strengths["general_knowledge"] = 0.7
            required_strengths["clarity"] = 0.6
        elif query_type == "opinion":
            required_strengths["critical_thinking"] = 0.8
            required_strengths["evaluation"] = 0.7
        elif query_type == "list":
            required_strengths["comprehensive"] = 0.7
            required_strengths["clarity"] = 0.6
            
        # Dựa vào yêu cầu định dạng
        format_reqs = query_analysis.get("format_requirements", {})
        if format_reqs.get("requires_step_by_step", False):
            required_strengths["clarity"] = 0.8
        if format_reqs.get("requires_examples", False):
            required_strengths["technical_explanation"] = 0.7
        if format_reqs.get("requires_comparison", False):
            required_strengths["balanced"] = 0.8
            required_strengths["analysis"] = 0.7
            
        # Xem xét lĩnh vực
        domain = query_analysis.get("domain", "")
        if domain == "technology":
            required_strengths["technical_explanation"] = 0.8
            required_strengths["programming"] = 0.7
        elif domain == "science":
            required_strengths["analysis"] = 0.8
            required_strengths["reasoning"] = 0.7
        elif domain == "business":
            required_strengths["analysis"] = 0.7
            required_strengths["balanced"] = 0.7
        elif domain == "arts":
            required_strengths["creative"] = 0.8
            
        return required_strengths
    
    def _calculate_model_score(self, model_strengths: Dict[str, float],
                              required_strengths: Dict[str, float]) -> float:
        """
        Tính điểm cho mô hình dựa trên điểm mạnh và yêu cầu
        
        Args:
            model_strengths: Điểm mạnh của mô hình
            required_strengths: Điểm mạnh cần thiết
            
        Returns:
            Điểm tổng hợp
        """
        score = 0.0
        total_weight = 0.0
        
        for category, importance in required_strengths.items():
            if importance > 0.1:  # Chỉ xem xét những điểm mạnh được ưu tiên
                strength = model_strengths.get(category, 0.5)
                score += strength * importance
                total_weight += importance
                
        # Nếu không có điểm mạnh nào được ưu tiên, sử dụng trung bình
        if total_weight == 0:
            return sum(model_strengths.values()) / len(model_strengths) if model_strengths else 0.5
            
        return score / total_weight
    
    def _update_performance_cache(self, query: str, model_name: str, 
                                feedback_score: Optional[float]) -> None:
        """
        Cập nhật bộ nhớ cache hiệu suất mô hình
        
        Args:
            query: Truy vấn người dùng
            model_name: Tên mô hình
            feedback_score: Điểm đánh giá
        """
        if feedback_score is None:
            return
            
        # Trích xuất từ khóa
        keywords = self._extract_keywords(query)
        query_type = self._infer_query_type(query)
        
        # Cập nhật cache cho từng từ khóa
        for keyword in keywords:
            if keyword not in self.model_performance_cache:
                self.model_performance_cache[keyword] = {}
                
            if model_name not in self.model_performance_cache[keyword]:
                self.model_performance_cache[keyword][model_name] = {
                    "score": 0.5,
                    "count": 0
                }
                
            current = self.model_performance_cache[keyword][model_name]
            new_score = (current["score"] * current["count"] + feedback_score) / (current["count"] + 1)
            
            self.model_performance_cache[keyword][model_name] = {
                "score": new_score,
                "count": current["count"] + 1
            }
            
        # Cập nhật cache cho loại truy vấn
        query_key = f"type:{query_type}"
        if query_key not in self.model_performance_cache:
            self.model_performance_cache[query_key] = {}
            
        if model_name not in self.model_performance_cache[query_key]:
            self.model_performance_cache[query_key][model_name] = {
                "score": 0.5,
                "count": 0
            }
            
        current = self.model_performance_cache[query_key][model_name]
        new_score = (current["score"] * current["count"] + feedback_score) / (current["count"] + 1)
        
        self.model_performance_cache[query_key][model_name] = {
            "score": new_score,
            "count": current["count"] + 1
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Trích xuất từ khóa từ truy vấn
        
        Args:
            query: Truy vấn người dùng
            
        Returns:
            Danh sách từ khóa
        """
        # Phương pháp đơn giản: tách từ và loại bỏ stop words
        stop_words = {"là", "và", "của", "cho", "trong", "một", "các", "những", 
                     "về", "với", "có", "được", "không", "như", "từ", "đến", 
                     "tôi", "bạn", "chúng", "mình", "để", "này", "khi", "làm"}
        
        # Chuyển thành chữ thường và tách từ
        words = query.lower().split()
        
        # Lọc bỏ stop words và từ ngắn
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _infer_query_type(self, query: str) -> str:
        """
        Suy luận loại truy vấn
        
        Args:
            query: Truy vấn người dùng
            
        Returns:
            Loại truy vấn
        """
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
        elif "?" in query:
            return "question"
        else:
            return "statement"
    
    def get_model_weights(self) -> Dict[str, float]:
        """
        Lấy trọng số hiện tại của các mô hình
        
        Returns:
            Dict chứa trọng số của mỗi mô hình
        """
        return self.model_weights.copy()
    
    def get_model_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy thống kê về hiệu suất mô hình
        
        Returns:
            Dict chứa thống kê về mỗi mô hình
        """
        stats = {}
        
        for model_name in self.model_weights.keys():
            stats[model_name] = {
                "weight": self.model_weights.get(model_name, self.default_weight),
                "win_rate": self.model_win_rate.get(model_name, 0.5),
                "avg_score": self.model_avg_score.get(model_name, 0.5),
                "selection_count": self.model_selection_count.get(model_name, 0),
                "strengths": self.model_strengths.get(model_name, {})
            }
            
        return stats
    
    def clear_cache(self) -> None:
        """Xóa bộ nhớ cache hiệu suất"""
        self.model_performance_cache.clear()
        
    def reset_weights(self) -> None:
        """Đặt lại trọng số về mặc định"""
        for model_name in self.model_weights.keys():
            self.model_weights[model_name] = self.default_weight