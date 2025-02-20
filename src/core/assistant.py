"""
Module cho lớp PersonalAssistant cơ bản
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from src.core.models import ModelManager

logger = logging.getLogger(__name__)

class PersonalAssistant:
    """
    PersonalAssistant cơ bản thực hiện:
    - Quản lý hội thoại
    - Định tuyến truy vấn đến mô hình thích hợp
    - Lưu lịch sử hội thoại
    - Quản lý ngữ cảnh
    """
    
    def __init__(self, model_manager: ModelManager, config: Dict[str, Any]):
        """
        Khởi tạo Personal Assistant
        
        Args:
            model_manager: Đối tượng quản lý mô hình
            config: Cấu hình hệ thống
        """
        self.model_manager = model_manager
        self.config = config
        self.assistant_config = config.get("assistant", {})
        
        # Lấy cấu hình
        self.default_max_tokens = self.assistant_config.get("default_max_tokens", 1024)
        self.default_temperature = self.assistant_config.get("default_temperature", 0.7)
        self.conversation_history_limit = self.assistant_config.get("conversation_history_limit", 100)
        
        # Đường dẫn lưu hội thoại
        self.conversation_dir = config.get("system", {}).get(
            "conversation_dir", "data/conversations")
        os.makedirs(self.conversation_dir, exist_ok=True)
        
        # Lịch sử hội thoại theo ID
        self.conversations = {}
        
        logger.info("Đã khởi tạo Personal Assistant")
        
    def get_response(self, query: str, conversation_id: Optional[str] = None,
                    user_info: Optional[Dict] = None, model_name: Optional[str] = None,
                    system_prompt: Optional[str] = None,
                    params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Nhận câu trả lời cho truy vấn
        
        Args:
            query: Truy vấn của người dùng
            conversation_id: ID của cuộc hội thoại (tùy chọn)
            user_info: Thông tin về người dùng (tùy chọn)
            model_name: Tên mô hình để sử dụng (tùy chọn)
            system_prompt: Ghi đè system prompt (tùy chọn)
            params: Tham số bổ sung cho mô hình (tùy chọn)
            
        Returns:
            Dict chứa câu trả lời và thông tin bổ sung
        """
        start_time = time.time()
        
        # Tạo ID cuộc hội thoại nếu chưa có
        if not conversation_id:
            conversation_id = f"conv_{int(time.time())}"
            
        # Khởi tạo lịch sử hội thoại nếu chưa có
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        # Chuẩn bị tham số mô hình
        model_params = {
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens
        }
        
        # Ghi đè tham số nếu được cung cấp
        if params:
            model_params.update(params)
            
        # Chọn mô hình mặc định nếu không được chỉ định
        if not model_name:
            model_name = self._select_default_model()
            
        # Tạo prompt với lịch sử hội thoại
        prompt_with_history = self._create_prompt_with_history(
            query, conversation_id, user_info)
            
        # Lấy câu trả lời từ mô hình
        response = self.model_manager.get_response(
            model_name, prompt_with_history, system_prompt, model_params)
            
        # Cập nhật lịch sử hội thoại
        self._update_conversation_history(
            conversation_id, query, response.get("response", ""))
            
        # Lưu hội thoại
        self._save_conversation(conversation_id)
        
        # Bổ sung thông tin vào kết quả
        response["conversation_id"] = conversation_id
        response["query"] = query
        response["total_time"] = time.time() - start_time
        
        return response
    
    def _select_default_model(self) -> str:
        """
        Chọn mô hình mặc định
        
        Returns:
            Tên mô hình mặc định
        """
        # Lấy danh sách mô hình
        models = self.model_manager.list_models()
        
        # Sử dụng mô hình đầu tiên nếu có
        if models:
            return models[0]
            
        # Mặc định
        return "deepseek-r1:1.5b"
    
    def _create_prompt_with_history(self, query: str, conversation_id: str,
                                  user_info: Optional[Dict] = None) -> str:
        """
        Tạo prompt kèm theo lịch sử hội thoại
        
        Args:
            query: Truy vấn của người dùng
            conversation_id: ID của cuộc hội thoại
            user_info: Thông tin về người dùng (tùy chọn)
            
        Returns:
            Prompt hoàn chỉnh
        """
        # Lấy lịch sử hội thoại
        history = self.conversations.get(conversation_id, [])
        
        # Giới hạn số lượng lịch sử
        limited_history = history[-self.conversation_history_limit:] if history else []
        
        # Tạo prompt với lịch sử
        prompt_parts = []
        
        # Thêm thông tin người dùng nếu có
        if user_info:
            user_context = f"Thông tin người dùng: {json.dumps(user_info, ensure_ascii=False)}"
            prompt_parts.append(user_context)
            
        # Thêm lịch sử hội thoại
        for entry in limited_history:
            if entry["role"] == "user":
                prompt_parts.append(f"Người dùng: {entry['content']}")
            else:
                prompt_parts.append(f"Trợ lý: {entry['content']}")
                
        # Thêm truy vấn hiện tại
        prompt_parts.append(f"Người dùng: {query}")
        prompt_parts.append("Trợ lý:")
        
        return "\n\n".join(prompt_parts)
    
    def _update_conversation_history(self, conversation_id: str, 
                                   query: str, response: str) -> None:
        """
        Cập nhật lịch sử hội thoại
        
        Args:
            conversation_id: ID của cuộc hội thoại
            query: Truy vấn của người dùng
            response: Câu trả lời từ trợ lý
        """
        # Đảm bảo conversation_id tồn tại
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            
        # Thêm truy vấn và câu trả lời
        self.conversations[conversation_id].append({
            "role": "user",
            "content": query,
            "timestamp": time.time()
        })
        
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": time.time()
        })
    
    def _save_conversation(self, conversation_id: str) -> None:
        """
        Lưu hội thoại vào file
        
        Args:
            conversation_id: ID của cuộc hội thoại
        """
        try:
            conversation = self.conversations.get(conversation_id, [])
            if not conversation:
                return
                
            file_path = os.path.join(self.conversation_dir, f"{conversation_id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "id": conversation_id,
                    "updated_at": time.time(),
                    "messages": conversation
                }, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Lỗi khi lưu hội thoại {conversation_id}: {e}")
    
    def load_conversation(self, conversation_id: str) -> bool:
        """
        Tải hội thoại từ file
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            True nếu tải thành công, False nếu không
        """
        try:
            file_path = os.path.join(self.conversation_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.conversations[conversation_id] = data.get("messages", [])
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi tải hội thoại {conversation_id}: {e}")
            return False
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử hội thoại
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            Danh sách các lượt trao đổi trong hội thoại
        """
        # Tải hội thoại nếu chưa có trong memory
        if conversation_id not in self.conversations:
            self.load_conversation(conversation_id)
            
        return self.conversations.get(conversation_id, []).copy()
    
    def list_conversations(self) -> List[str]:
        """
        Lấy danh sách ID các cuộc hội thoại đã lưu
        
        Returns:
            Danh sách ID cuộc hội thoại
        """
        try:
            files = os.listdir(self.conversation_dir)
            conversation_ids = [f.replace(".json", "") for f in files if f.endswith(".json")]
            return conversation_ids
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách hội thoại: {e}")
            return []
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Xóa lịch sử hội thoại
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            True nếu xóa thành công, False nếu không
        """
        try:
            # Xóa khỏi memory
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                
            # Xóa file
            file_path = os.path.join(self.conversation_dir, f"{conversation_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi xóa hội thoại {conversation_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về trợ lý
        
        Returns:
            Dict chứa các thống kê
        """
        try:
            # Đếm tổng số hội thoại
            conversation_files = self.list_conversations()
            
            # Đếm tổng số lượt trao đổi
            total_exchanges = 0
            for conv_id in self.conversations.keys():
                total_exchanges += len(self.conversations[conv_id]) // 2
                
            # Thống kê từ model manager
            model_stats = self.model_manager.get_performance_stats()
            
            return {
                "total_conversations": len(conversation_files),
                "active_conversations": len(self.conversations),
                "total_exchanges": total_exchanges,
                "model_stats": model_stats
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy thống kê: {e}")
            return {}