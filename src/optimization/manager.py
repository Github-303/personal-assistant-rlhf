"""
Module quản lý tối ưu hóa phản hồi dựa trên RLHF và DPO
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple

from src.optimization.feedback_collector import FeedbackCollector
from src.optimization.feedback_store import FeedbackStore
from src.optimization.preference_optimizer import PreferenceOptimizer
from src.optimization.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

class FeedbackOptimizationManager:
    """
    Quản lý quy trình tối ưu hóa phản hồi bằng cách phối hợp giữa:
    - Thu thập phản hồi (RLHF)
    - Tối ưu hóa dựa trên tỷ lệ thắng (DPO)
    - Phân tích và tối ưu hóa truy vấn/câu trả lời
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo Feedback Optimization Manager
        
        Args:
            config: Cấu hình hệ thống
        """
        self.config = config
        self.optimization_config = config.get("optimization", {})
        self.enabled = self.optimization_config.get("enabled", True)
        
        # Khởi tạo các thành phần
        feedback_db_path = config.get("system", {}).get("feedback_db", "data/feedback.db")
        os.makedirs(os.path.dirname(feedback_db_path), exist_ok=True)
        
        # Khởi tạo kho lưu trữ phản hồi
        self.feedback_store = FeedbackStore(feedback_db_path)
        
        # Khởi tạo bộ tối ưu hóa sở thích
        self.preference_optimizer = PreferenceOptimizer(config)
        
        # Khởi tạo bộ thu thập phản hồi
        self.feedback_collector = FeedbackCollector(
            self.feedback_store,
            config
        )
        
        # Khởi tạo bộ tối ưu hóa câu trả lời
        self.response_optimizer = ResponseOptimizer(config)
        
        logger.info("Đã khởi tạo Feedback Optimization Manager")
        
    def optimize_query(self, query: str, user_info: Optional[Dict] = None, 
                      conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Tối ưu hóa truy vấn người dùng
        
        Args:
            query: Câu hỏi của người dùng
            user_info: Thông tin về người dùng (tùy chọn)
            conversation_history: Lịch sử hội thoại (tùy chọn)
            
        Returns:
            Dict chứa kết quả phân tích và prompt đã được tối ưu
        """
        if not self.enabled:
            return {'analysis': {}, 'optimized_prompt': query}
            
        try:
            # Sử dụng phương thức đúng từ ResponseOptimizer 
            result = self.response_optimizer.optimize_query(query, user_info, conversation_history)
            return result
        except Exception as e:
            logger.error(f"Lỗi khi tối ưu hóa truy vấn: {e}")
            return {'analysis': {}, 'optimized_prompt': query}
    
    def select_best_model(self, query: str, analysis: Optional[Dict] = None,
                         available_models: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Chọn mô hình tốt nhất dựa trên phân tích truy vấn
        
        Args:
            query: Truy vấn người dùng
            analysis: Kết quả phân tích truy vấn (tùy chọn)
            available_models: Danh sách mô hình khả dụng (tùy chọn)
            
        Returns:
            Tên của mô hình được chọn hoặc None
        """
        if not self.enabled:
            return None
            
        try:
            # Phân tích truy vấn nếu chưa có
            if analysis is None:
                analysis = self.response_optimizer.analyze_query(query)
                
            # Lấy các mô hình khả dụng nếu chưa có
            if available_models is None:
                available_models = self.config.get("models", [])
                
            # Chọn mô hình tốt nhất bằng PreferenceOptimizer
            best_model = self.preference_optimizer.select_best_model(
                analysis, available_models)
                
            return best_model
        except Exception as e:
            logger.error(f"Lỗi khi chọn mô hình tốt nhất: {e}")
            return None
    
    def process_feedback(self, conversation_id: str, query: str, responses: Dict[str, str],
                        selected_response: str, feedback_score: Optional[float] = None,
                        feedback_text: Optional[str] = None) -> bool:
        """
        Xử lý phản hồi của người dùng và cập nhật các mô hình tối ưu
        
        Args:
            conversation_id: ID của cuộc hội thoại
            query: Truy vấn người dùng
            responses: Dict các câu trả lời với key là model_name
            selected_response: Tên mô hình được chọn
            feedback_score: Điểm đánh giá (0-1, tùy chọn)
            feedback_text: Phản hồi dạng văn bản (tùy chọn)
            
        Returns:
            True nếu xử lý thành công, False nếu không
        """
        if not self.enabled:
            return False
            
        try:
            # Lưu phản hồi vào kho lưu trữ
            feedback_id = self.feedback_collector.collect_feedback(
                conversation_id=conversation_id,
                query=query,
                responses=responses,
                selected_response=selected_response,
                feedback_score=feedback_score,
                feedback_text=feedback_text
            )
            
            if feedback_id:
                # Cập nhật trọng số sở thích
                self.preference_optimizer.update_weights_from_feedback(
                    query, responses, selected_response, feedback_score
                )
                
                # Cập nhật hiệu suất mẫu prompt
                self._update_template_performance(query, selected_response, feedback_score)
                
                return True
                
            return False
        except Exception as e:
            logger.error(f"Lỗi khi xử lý phản hồi: {e}")
            return False
    
    def _update_template_performance(self, query: str, selected_model: str, 
                                    feedback_score: Optional[float]) -> None:
        """
        Cập nhật hiệu suất mẫu prompt dựa trên phản hồi
        
        Args:
            query: Truy vấn người dùng
            selected_model: Mô hình được chọn
            feedback_score: Điểm đánh giá
        """
        if feedback_score is None:
            return
            
        # Lấy thông tin về mẫu prompt được sử dụng
        query_result = self.response_optimizer.query_analysis_cache.get(query, {})
        template_used = query_result.get("template_used", "default")
        
        # Cập nhật hiệu suất mẫu
        self.response_optimizer.update_template_performance(template_used, feedback_score)
    
    def export_feedback_data(self, export_dir: Optional[str] = None) -> str:
        """
        Xuất dữ liệu phản hồi để huấn luyện RLHF
        
        Args:
            export_dir: Thư mục xuất dữ liệu (tùy chọn)
            
        Returns:
            Đường dẫn đến file xuất
        """
        if export_dir is None:
            export_dir = self.config.get("system", {}).get(
                "rlhf_export_dir", "data/rlhf_exports")
                
        os.makedirs(export_dir, exist_ok=True)
        
        try:
            export_path = self.feedback_collector.export_feedback_data(export_dir)
            return export_path
        except Exception as e:
            logger.error(f"Lỗi khi xuất dữ liệu phản hồi: {e}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về dữ liệu phản hồi và tối ưu hóa
        
        Returns:
            Dict chứa các thống kê
        """
        stats = {
            "enabled": self.enabled,
            "feedback_collection": {
                "total_samples": self.feedback_store.get_total_count(),
                "positive_samples": self.feedback_store.get_count_by_score(min_score=0.7),
                "negative_samples": self.feedback_store.get_count_by_score(max_score=0.3),
                "neutral_samples": self.feedback_store.get_count_by_score(min_score=0.3, max_score=0.7)
            },
            "model_preferences": self.preference_optimizer.get_model_weights(),
            "template_performance": self.response_optimizer.template_performance_history
        }
        
        return stats
    
    def toggle_optimization(self, enabled: bool) -> None:
        """
        Bật/tắt tối ưu hóa
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.enabled = enabled
        
    def toggle_feedback_collection(self, enabled: bool) -> None:
        """
        Bật/tắt thu thập phản hồi
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.feedback_collector.toggle_collection(enabled)
        
    def clear_caches(self) -> None:
        """Xóa tất cả bộ nhớ cache"""
        self.response_optimizer.clear_cache()
        self.preference_optimizer.clear_cache()