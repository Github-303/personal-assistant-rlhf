"""
Module quản lý thảo luận nhóm giữa các mô hình LLM
"""

import os
import time
import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Union

from src.core.models import ModelManager

logger = logging.getLogger(__name__)

class GroupDiscussionManager:
    """
    Quản lý thảo luận nhóm giữa nhiều mô hình LLM.
    Thực hiện:
    - Điều phối luồng thảo luận
    - Tích hợp các phản hồi
    - Tổng hợp kết quả cuối cùng
    """
    
    def __init__(self, model_manager: ModelManager, config: Dict[str, Any]):
        """
        Khởi tạo Group Discussion Manager
        
        Args:
            model_manager: Đối tượng quản lý mô hình
            config: Cấu hình hệ thống
        """
        self.model_manager = model_manager
        self.config = config
        self.group_config = config.get("group_discussion", {})
        
        # Lấy cấu hình
        self.name = self.group_config.get("name", "group_discussion")
        self.system_prompt = self.group_config.get("system_prompt", 
            "Đây là kết quả thảo luận nhóm giữa các AI chuyên gia khác nhau. "
            "Mỗi chuyên gia đã đóng góp từ lĩnh vực chuyên môn của họ, và "
            "kết quả đã được tổng hợp thành một câu trả lời toàn diện.")
        self.default_rounds = self.group_config.get("default_rounds", 2)
        
        # Lưu trữ thảo luận
        self.discussions = {}
        
        logger.info("Đã khởi tạo Group Discussion Manager")
        
    def conduct_discussion(self, query: str, discussion_id: Optional[str] = None,
                          user_info: Optional[Dict] = None, models: Optional[List[str]] = None,
                          params: Optional[Dict[str, Any]] = None,
                          rounds: Optional[int] = None) -> Dict[str, Any]:
        """
        Tiến hành thảo luận nhóm
        
        Args:
            query: Truy vấn của người dùng
            discussion_id: ID của cuộc thảo luận (tùy chọn)
            user_info: Thông tin về người dùng (tùy chọn)
            models: Danh sách mô hình tham gia (tùy chọn)
            params: Tham số bổ sung (tùy chọn)
            rounds: Số vòng thảo luận (tùy chọn)
            
        Returns:
            Dict chứa kết quả thảo luận và thông tin bổ sung
        """
        start_time = time.time()
        
        # Tạo ID cuộc thảo luận nếu chưa có
        if not discussion_id:
            discussion_id = f"disc_{int(time.time())}"
            
        # Số vòng thảo luận
        rounds = rounds or self.default_rounds
        
        # Chọn các mô hình tham gia
        participating_models = self._select_participating_models(models)
        if not participating_models:
            return {
                "error": "Không tìm thấy mô hình phù hợp cho thảo luận",
                "success": False
            }
            
        # Chuẩn bị tham số
        discussion_params = {
            "temperature": 0.7,
            "max_tokens": 1024
        }
        if params:
            discussion_params.update(params)
            
        # Tiến hành các vòng thảo luận
        discussion_log = []
        current_context = query
        models_used = set()
        
        for round_num in range(rounds):
            round_responses = {}
            
            # Lấy phản hồi từ mỗi mô hình
            for model_name in participating_models:
                try:
                    response = self.model_manager.get_response(
                        model_name,
                        current_context,
                        self._create_expert_system_prompt(model_name, round_num),
                        discussion_params
                    )
                    
                    round_responses[model_name] = response.get("response", "")
                    models_used.add(model_name)
                    
                except Exception as e:
                    logger.error(f"Lỗi khi lấy phản hồi từ {model_name}: {e}")
                    
            # Thêm vào log thảo luận
            discussion_log.append({
                "round": round_num + 1,
                "responses": round_responses
            })
            
            # Cập nhật ngữ cảnh cho vòng tiếp theo
            if round_num < rounds - 1:
                current_context = self._create_next_round_context(
                    query, round_responses, round_num)
                    
        # Tổng hợp kết quả cuối cùng
        final_response = self._synthesize_final_response(query, discussion_log)
        
        # Lưu thảo luận
        self._save_discussion(discussion_id, query, discussion_log, final_response)
        
        # Thời gian hoàn thành
        completion_time = time.time() - start_time
        
        # Kết quả
        result = {
            "response": final_response,
            "discussion_id": discussion_id,
            "models_used": list(models_used),
            "rounds": rounds,
            "completion_time": completion_time,
            "success": True
        }
        
        return result
    
    def _select_participating_models(self, specified_models: Optional[List[str]] = None) -> List[str]:
        """
        Chọn các mô hình tham gia thảo luận
        
        Args:
            specified_models: Danh sách mô hình được chỉ định (tùy chọn)
            
        Returns:
            Danh sách tên mô hình tham gia
        """
        if specified_models:
            # Lọc ra các mô hình tồn tại
            available_models = self.model_manager.list_models()
            return [model for model in specified_models if model in available_models]
            
        # Mặc định lấy tất cả mô hình
        return self.model_manager.list_models()
    
    def _create_expert_system_prompt(self, model_name: str, round_num: int) -> str:
        """
        Tạo system prompt cho mô hình chuyên gia
        
        Args:
            model_name: Tên mô hình
            round_num: Số thứ tự vòng thảo luận
            
        Returns:
            System prompt cho mô hình
        """
        # Lấy thông tin về mô hình
        model_info = self.model_manager.get_model_info(model_name)
        if not model_info:
            return ""
            
        # Lấy role và system prompt của mô hình
        role = model_info.get("role", "assistant")
        base_prompt = model_info.get("system_prompt", "")
        
        # Tạo prompt dựa trên vòng thảo luận
        if round_num == 0:
            # Vòng đầu: phản hồi ban đầu
            return (f"{base_prompt}\n\nBạn đang tham gia thảo luận nhóm với vai trò chuyên gia {role}. "
                   f"Hãy trả lời câu hỏi dựa trên chuyên môn của bạn. "
                   f"Tập trung vào những điểm mạnh của bạn như một chuyên gia {role}.")
        else:
            # Vòng sau: phản hồi và tổng hợp
            return (f"{base_prompt}\n\nBạn đang tham gia thảo luận nhóm với vai trò chuyên gia {role}. "
                   f"Hãy xem xét các ý kiến từ các chuyên gia khác và bổ sung thông tin từ góc nhìn chuyên môn của bạn. "
                   f"Tập trung vào việc cải thiện câu trả lời dựa trên chuyên môn {role}.")
    
    def _create_next_round_context(self, query: str, round_responses: Dict[str, str], 
                                 round_num: int) -> str:
        """
        Tạo ngữ cảnh cho vòng thảo luận tiếp theo
        
        Args:
            query: Truy vấn ban đầu
            round_responses: Phản hồi của vòng hiện tại
            round_num: Số thứ tự vòng hiện tại
            
        Returns:
            Ngữ cảnh cho vòng tiếp theo
        """
        context_parts = [
            f"Câu hỏi gốc: {query}",
            f"\nVòng thảo luận {round_num + 1} đã hoàn thành. Dưới đây là ý kiến của các chuyên gia:"
        ]
        
        # Thêm phản hồi từ mỗi mô hình
        for model, response in round_responses.items():
            model_info = self.model_manager.get_model_info(model)
            role = model_info.get("role", "assistant") if model_info else "assistant"
            
            context_parts.append(f"\n--- Ý kiến từ chuyên gia {role} ---")
            context_parts.append(response)
            
        # Hướng dẫn cho vòng tiếp theo
        context_parts.append(f"\n\nVòng thảo luận {round_num + 2}:")
        context_parts.append("Hãy xem xét các ý kiến trên và bổ sung thông tin từ góc nhìn chuyên môn của bạn.")
        context_parts.append("Tập trung vào việc cải thiện và làm rõ các điểm chưa được đề cập hoặc cần bổ sung.")
        
        return "\n".join(context_parts)
    
    def _synthesize_final_response(self, query: str, discussion_log: List[Dict[str, Any]]) -> str:
        """
        Tổng hợp câu trả lời cuối cùng từ thảo luận
        
        Args:
            query: Truy vấn ban đầu
            discussion_log: Nhật ký thảo luận
            
        Returns:
            Câu trả lời tổng hợp
        """
        # Không có thảo luận
        if not discussion_log:
            return "Không có đủ dữ liệu thảo luận để tổng hợp câu trả lời."
            
        # Lấy vòng cuối cùng
        last_round = discussion_log[-1]
        last_responses = last_round.get("responses", {})
        
        if not last_responses:
            return "Không có phản hồi trong vòng thảo luận cuối cùng."
            
        # Tạo prompt tổng hợp
        synthesis_prompt = [
            f"Câu hỏi: {query}",
            "\nThảo luận nhóm đã diễn ra giữa các chuyên gia. Dưới đây là ý kiến cuối cùng của họ:"
        ]
        
        for model, response in last_responses.items():
            model_info = self.model_manager.get_model_info(model)
            role = model_info.get("role", "assistant") if model_info else "assistant"
            
            synthesis_prompt.append(f"\n--- Chuyên gia {role} ---")
            synthesis_prompt.append(response)
            
        synthesis_prompt.append("\nHãy tổng hợp các ý kiến trên thành một câu trả lời toàn diện và cân bằng.")
        
        # Sử dụng một mô hình để tổng hợp
        synthesis_model = self._select_synthesis_model(last_responses.keys())
        
        try:
            result = self.model_manager.get_response(
                synthesis_model,
                "\n".join(synthesis_prompt),
                self.system_prompt,
                {"temperature": 0.5, "max_tokens": 1536}
            )
            
            return result.get("response", "Không thể tổng hợp câu trả lời.")
            
        except Exception as e:
            logger.error(f"Lỗi khi tổng hợp câu trả lời: {e}")
            
            # Fallback: ghép các phản hồi
            combined_response = "\n\n".join([
                f"Từ góc nhìn {self.model_manager.get_model_info(model).get('role', 'chuyên gia') if self.model_manager.get_model_info(model) else 'chuyên gia'}:\n{response}"
                for model, response in last_responses.items()
            ])
            
            return combined_response
    
    def _select_synthesis_model(self, participating_models: List[str]) -> str:
        """
        Chọn mô hình để tổng hợp câu trả lời cuối cùng
        
        Args:
            participating_models: Danh sách mô hình đã tham gia
            
        Returns:
            Tên mô hình được chọn
        """
        # Ưu tiên mô hình có vai trò deep_thinking
        all_models = self.model_manager.list_models()
        
        for model in all_models:
            model_info = self.model_manager.get_model_info(model)
            if model_info and model_info.get("role") == "deep_thinking":
                return model
                
        # Nếu không có, chọn ngẫu nhiên từ danh sách tham gia
        if participating_models:
            return random.choice(list(participating_models))
            
        # Mặc định: mô hình đầu tiên
        return all_models[0] if all_models else "deepseek-r1:8b"
    
    def _save_discussion(self, discussion_id: str, query: str, 
                       discussion_log: List[Dict[str, Any]], final_response: str) -> None:
        """
        Lưu thảo luận
        
        Args:
            discussion_id: ID của cuộc thảo luận
            query: Truy vấn ban đầu
            discussion_log: Nhật ký thảo luận
            final_response: Câu trả lời cuối cùng
        """
        # Lưu vào memory
        self.discussions[discussion_id] = {
            "id": discussion_id,
            "query": query,
            "log": discussion_log,
            "final_response": final_response,
            "timestamp": time.time()
        }
    
    def get_discussion(self, discussion_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin về cuộc thảo luận
        
        Args:
            discussion_id: ID của cuộc thảo luận
            
        Returns:
            Dict chứa thông tin thảo luận hoặc None nếu không tìm thấy
        """
        return self.discussions.get(discussion_id)
    
    def list_discussions(self) -> List[str]:
        """
        Lấy danh sách ID các cuộc thảo luận
        
        Returns:
            Danh sách ID cuộc thảo luận
        """
        return list(self.discussions.keys())
    
    def clear_discussions(self) -> None:
        """Xóa tất cả dữ liệu thảo luận"""
        self.discussions.clear()