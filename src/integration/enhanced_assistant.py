"""
Tích hợp các thành phần thành một trợ lý nâng cao với RLHF và DPO
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union

from src.core.assistant import PersonalAssistant
from src.core.group_discussion import GroupDiscussionManager
from src.optimization.manager import FeedbackOptimizationManager

logger = logging.getLogger(__name__)

class EnhancedPersonalAssistant:
    """
    Trợ lý cá nhân nâng cao tích hợp:
    - Trợ lý cơ bản
    - Thảo luận nhóm
    - Tối ưu hóa phản hồi (RLHF/DPO)
    - Tự động chọn mô hình
    """
    
    def __init__(self, base_assistant: PersonalAssistant,
                group_discussion_manager: GroupDiscussionManager,
                feedback_manager: FeedbackOptimizationManager,
                config: Dict[str, Any]):
        """
        Khởi tạo Enhanced Personal Assistant
        
        Args:
            base_assistant: Đối tượng PersonalAssistant cơ bản
            group_discussion_manager: Đối tượng GroupDiscussionManager
            feedback_manager: Đối tượng FeedbackOptimizationManager
            config: Cấu hình hệ thống
        """
        self.assistant = base_assistant
        self.group_manager = group_discussion_manager
        self.feedback_manager = feedback_manager
        self.config = config
        
        # Cấu hình từ optimization
        self.optimization_enabled = config.get("optimization", {}).get("enabled", True)
        self.auto_select_model = config.get("optimization", {}).get("auto_select_model", True)
        self.use_group_discussion = config.get("optimization", {}).get("check_group_discussion_suitability", False)
        
        # Cấu hình thu thập phản hồi
        self.feedback_collection_enabled = config.get("optimization", {}).get(
            "feedback", {}).get("enabled", True)
        
        # Thông tin hội thoại hiện tại
        self.current_conversation_id = None
        self.conversation_history = []
        
        # Bộ nhớ cache cho các câu trả lời
        self.response_cache = {}
        
        logger.info("Đã khởi tạo Enhanced Personal Assistant với RLHF và DPO")
        
    def get_response(self, query: str, conversation_id: Optional[str] = None,
                    user_info: Optional[Dict] = None, model_name: Optional[str] = None,
                    use_group_discussion: Optional[bool] = None,
                    system_prompt: Optional[str] = None,
                    params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Nhận câu trả lời cho truy vấn với tối ưu hóa tự động
        
        Args:
            query: Truy vấn của người dùng
            conversation_id: ID của cuộc hội thoại (tùy chọn)
            user_info: Thông tin về người dùng (tùy chọn)
            model_name: Tên mô hình để sử dụng (tùy chọn)
            use_group_discussion: Ghi đè cấu hình sử dụng thảo luận nhóm (tùy chọn)
            system_prompt: Ghi đè system prompt (tùy chọn)
            params: Tham số bổ sung cho mô hình (tùy chọn)
            
        Returns:
            Dict chứa câu trả lời và thông tin bổ sung
        """
        start_time = time.time()
        
        # Thiết lập cuộc hội thoại
        conversation_id = conversation_id or self.current_conversation_id or f"conv_{int(time.time())}"
        self.current_conversation_id = conversation_id
        
        # Tối ưu hóa truy vấn nếu được bật
        optimized_query = query
        query_analysis = {}
        
        if self.optimization_enabled:
            try:
                optimization_result = self.feedback_manager.optimize_query(
                    query, user_info, self.conversation_history)
                
                if optimization_result:
                    optimized_query = optimization_result.get("optimized_prompt", query)
                    query_analysis = optimization_result.get("analysis", {})
            except Exception as e:
                logger.error(f"Lỗi khi tối ưu hóa truy vấn: {e}")
        
        # Tự động chọn mô hình nếu được bật và không có mô hình cụ thể
        selected_model = model_name
        model_selection_info = {}
        
        if self.auto_select_model and not selected_model:
            try:
                selected_model = self.feedback_manager.select_best_model(
                    query, query_analysis)
                
                if selected_model:
                    logger.info(f"Tự động chọn mô hình {selected_model} dựa trên phân tích câu hỏi")
                    model_selection_info = {
                        "auto_selected": True,
                        "model": selected_model,
                        "reason": "Dựa trên phân tích điểm mạnh của mô hình và yêu cầu của câu hỏi"
                    }
            except Exception as e:
                logger.error(f"Lỗi khi tự động chọn mô hình: {e}")
        
        # Xác định xem có nên sử dụng thảo luận nhóm hay không
        should_use_group = use_group_discussion if use_group_discussion is not None else self.use_group_discussion
        group_discussion_used = False
        group_discussion_info = {}
        
        if should_use_group and self._is_suitable_for_group_discussion(query, query_analysis):
            try:
                group_result = self.group_manager.conduct_discussion(
                    optimized_query, conversation_id, user_info, None, params)
                
                response_text = group_result.get("response", "")
                group_discussion_used = True
                group_discussion_info = {
                    "rounds": group_result.get("rounds", 0),
                    "models_used": group_result.get("models_used", []),
                    "completion_time": group_result.get("completion_time", 0)
                }
            except Exception as e:
                logger.error(f"Lỗi khi thực hiện thảo luận nhóm: {e}")
                # Quay lại sử dụng mô hình đơn nếu thảo luận nhóm thất bại
                group_discussion_used = False
        
        # Nếu không sử dụng thảo luận nhóm, sử dụng câu trả lời từ mô hình đơn
        if not group_discussion_used:
            try:
                response = self.assistant.get_response(
                    optimized_query, conversation_id, user_info,
                    selected_model, system_prompt, params)
                
                response_text = response.get("response", "")
            except Exception as e:
                logger.error(f"Lỗi khi lấy câu trả lời từ assistant: {e}")
                response_text = f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Chi tiết lỗi: {str(e)}"
        
        # Cập nhật lịch sử hội thoại
        self._update_conversation_history(query, response_text)
        
        # Chuẩn bị kết quả trả về
        completion_time = time.time() - start_time
        
        result = {
            "response": response_text,
            "conversation_id": conversation_id,
            "completion_time": completion_time,
            "model_used": selected_model or "default",
            "optimized": self.optimization_enabled,
            "auto_model_selection": model_selection_info if self.auto_select_model else {},
            "group_discussion": group_discussion_info if group_discussion_used else {},
            "query_analysis": query_analysis if self.optimization_enabled else {}
        }
        
        # Lưu kết quả vào cache
        self._cache_response(query, result)
        
        return result
    
    def provide_feedback(self, query: str, selected_response: str, 
                        feedback_score: Optional[float] = None,
                        feedback_text: Optional[str] = None) -> bool:
        """
        Cung cấp phản hồi về câu trả lời
        
        Args:
            query: Truy vấn ban đầu
            selected_response: Câu trả lời được chọn
            feedback_score: Điểm đánh giá (0-1, tùy chọn)
            feedback_text: Phản hồi dạng văn bản (tùy chọn)
            
        Returns:
            True nếu phản hồi được xử lý thành công, False nếu không
        """
        if not self.feedback_collection_enabled or not self.current_conversation_id:
            return False
            
        # Lấy các câu trả lời từ cache
        cached_responses = self._get_cached_responses(query)
        if not cached_responses:
            return False
            
        # Xử lý phản hồi thông qua FeedbackOptimizationManager
        success = self.feedback_manager.process_feedback(
            conversation_id=self.current_conversation_id,
            query=query,
            responses=cached_responses,
            selected_response=selected_response,
            feedback_score=feedback_score,
            feedback_text=feedback_text
        )
        
        return success
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Lấy lịch sử hội thoại hiện tại
        
        Returns:
            Danh sách các dict chứa thông tin về mỗi lượt trao đổi
        """
        return self.conversation_history.copy()
    
    def clear_conversation(self) -> None:
        """Xóa lịch sử hội thoại và tạo cuộc hội thoại mới"""
        self.current_conversation_id = f"conv_{int(time.time())}"
        self.conversation_history = []
        self.response_cache = {}
        
    def toggle_optimization(self, enabled: bool) -> None:
        """
        Bật/tắt tối ưu hóa
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.optimization_enabled = enabled
        self.feedback_manager.toggle_optimization(enabled)
        
    def toggle_auto_select_model(self, enabled: bool) -> None:
        """
        Bật/tắt tự động chọn mô hình
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.auto_select_model = enabled
        
    def toggle_feedback_collection(self, enabled: bool) -> None:
        """
        Bật/tắt thu thập phản hồi
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.feedback_collection_enabled = enabled
        self.feedback_manager.toggle_feedback_collection(enabled)
        
    def toggle_group_discussion(self, enabled: bool) -> None:
        """
        Bật/tắt sử dụng thảo luận nhóm
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.use_group_discussion = enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về hệ thống
        
        Returns:
            Dict chứa các thống kê
        """
        # Lấy thống kê từ các thành phần
        optimization_stats = self.feedback_manager.get_stats()
        
        stats = {
            "optimization": {
                "enabled": self.optimization_enabled,
                "auto_select_model": self.auto_select_model,
                "feedback_collection": self.feedback_collection_enabled,
                "use_group_discussion": self.use_group_discussion,
                **optimization_stats
            },
            "conversation": {
                "current_id": self.current_conversation_id,
                "history_length": len(self.conversation_history),
                "cached_responses": len(self.response_cache)
            }
        }
        
        return stats
    
    def export_feedback_data(self, export_dir: Optional[str] = None) -> str:
        """
        Xuất dữ liệu phản hồi để huấn luyện RLHF
        
        Args:
            export_dir: Thư mục xuất dữ liệu (tùy chọn)
            
        Returns:
            Đường dẫn đến file xuất
        """
        return self.feedback_manager.export_feedback_data(export_dir)
    
    def _update_conversation_history(self, query: str, response: str) -> None:
        """
        Cập nhật lịch sử hội thoại
        
        Args:
            query: Truy vấn của người dùng
            response: Câu trả lời từ trợ lý
        """
        # Giới hạn số lượng mục trong lịch sử
        max_history = self.config.get("assistant", {}).get("conversation_history_limit", 100)
        
        # Thêm lượt trao đổi mới
        self.conversation_history.append({
            "role": "user",
            "content": query,
            "timestamp": time.time()
        })
        
        self.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": time.time()
        })
        
        # Cắt bớt nếu quá dài
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]
    
    def _cache_response(self, query: str, result: Dict[str, Any]) -> None:
        """
        Lưu cache câu trả lời
        
        Args:
            query: Truy vấn của người dùng
            result: Kết quả từ trợ lý
        """
        model_used = result.get("model_used", "default")
        response = result.get("response", "")
        
        if query not in self.response_cache:
            self.response_cache[query] = {}
            
        self.response_cache[query][model_used] = response
    
    def _get_cached_responses(self, query: str) -> Dict[str, str]:
        """
        Lấy các câu trả lời đã lưu trong cache
        
        Args:
            query: Truy vấn của người dùng
            
        Returns:
            Dict các câu trả lời với key là model_name
        """
        return self.response_cache.get(query, {})
    
    def _is_suitable_for_group_discussion(self, query: str, 
                                         analysis: Optional[Dict] = None) -> bool:
        """
        Kiểm tra xem truy vấn có phù hợp cho thảo luận nhóm hay không
        
        Args:
            query: Truy vấn của người dùng
            analysis: Kết quả phân tích truy vấn (tùy chọn)
            
        Returns:
            True nếu phù hợp, False nếu không
        """
        # Không có phân tích, sử dụng phân tích đơn giản
        if not analysis:
            # Truy vấn dài và phức tạp hơn thường phù hợp cho thảo luận nhóm
            is_complex = len(query) > 100 and ('?' in query or 'tại sao' in query.lower())
            return is_complex
            
        # Sử dụng phân tích đã có
        complexity = analysis.get("complexity", 0)
        requires_reasoning = analysis.get("requires_reasoning", False)
        requires_creativity = analysis.get("requires_creativity", False)
        
        # Truy vấn phức tạp, đòi hỏi suy luận hoặc sáng tạo phù hợp cho thảo luận nhóm
        return complexity > 6 or requires_reasoning or requires_creativity