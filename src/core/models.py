"""
Module quản lý các mô hình AI và tương tác với Ollama API
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Quản lý các mô hình AI và tương tác với Ollama API.
    Hỗ trợ:
    - Tải và quản lý mô hình 
    - Tạo truy vấn đến Ollama API
    - Quản lý bộ đệm và retry logic
    - Theo dõi hiệu suất mô hình
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Khởi tạo Model Manager
        
        Args:
            config: Cấu hình hệ thống
        """
        self.config = config
        self.ollama_config = config.get("ollama", {})
        
        # Cấu hình Ollama API
        self.base_url = self.ollama_config.get("base_url", "http://localhost:11434")
        self.timeout = self.ollama_config.get("timeout", 30)
        self.retry_attempts = self.ollama_config.get("retry_attempts", 3)
        
        # Danh sách mô hình
        self.models = self._load_models()
        
        # Bộ đệm cho kết quả truy vấn
        self.response_cache = {}
        
        # Thông tin hiệu suất
        self.performance_stats = {}
        
        logger.info(f"Đã khởi tạo ModelManager với {len(self.models)} mô hình")
        
    def _load_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Tải thông tin các mô hình từ cấu hình
        
        Returns:
            Dict chứa thông tin các mô hình
        """
        models_dict = {}
        
        # Tải từ cấu hình
        models_config = self.config.get("models", [])
        for model_config in models_config:
            model_name = model_config.get("name")
            if model_name:
                models_dict[model_name] = model_config
                
        return models_dict
    
    def list_models(self) -> List[str]:
        """
        Lấy danh sách tên các mô hình hiện có
        
        Returns:
            Danh sách tên các mô hình
        """
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin về mô hình
        
        Args:
            model_name: Tên mô hình
            
        Returns:
            Dict chứa thông tin mô hình hoặc None nếu không tìm thấy
        """
        return self.models.get(model_name)
    
    def get_response(self, model_name: str, prompt: str, 
                   system_prompt: Optional[str] = None,
                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Lấy câu trả lời từ mô hình
        
        Args:
            model_name: Tên mô hình
            prompt: Truy vấn người dùng
            system_prompt: System prompt (tùy chọn)
            params: Tham số bổ sung (tùy chọn)
            
        Returns:
            Dict chứa câu trả lời và thông tin bổ sung
        """
        # Kiểm tra xem mô hình có tồn tại không
        if model_name not in self.models:
            return {
                "response": f"Lỗi: Mô hình '{model_name}' không tồn tại",
                "error": f"Model '{model_name}' not found",
                "success": False
            }
            
        # Lấy system prompt từ cấu hình mô hình nếu không được cung cấp
        if system_prompt is None:
            system_prompt = self.models[model_name].get("system_prompt", "")
            
        # Chuẩn bị tham số
        model_params = {
            "temperature": self.config.get("assistant", {}).get("default_temperature", 0.7),
            "max_tokens": self.config.get("assistant", {}).get("default_max_tokens", 1024)
        }
        
        # Ghi đè tham số nếu được cung cấp
        if params:
            model_params.update(params)
            
        # Kiểm tra bộ đệm
        cache_key = f"{model_name}:{system_prompt}:{prompt}:{json.dumps(model_params)}"
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
            
        # Gửi truy vấn đến API
        start_time = time.time()
        try:
            response = self._query_ollama(model_name, prompt, system_prompt, model_params)
            
            # Tính thời gian hoàn thành
            completion_time = time.time() - start_time
            
            # Kết quả trả về
            result = {
                "response": response.get("response", ""),
                "model": model_name,
                "completion_time": completion_time,
                "success": True,
                "tokens": response.get("eval_count", 0)
            }
            
            # Cập nhật thống kê hiệu suất
            self._update_performance_stats(model_name, completion_time, 
                                         response.get("eval_count", 0))
            
            # Lưu vào bộ đệm
            self.response_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy câu trả lời từ mô hình {model_name}: {e}")
            
            # Kết quả lỗi
            error_result = {
                "response": f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu. Chi tiết: {str(e)}",
                "error": str(e),
                "model": model_name,
                "completion_time": time.time() - start_time,
                "success": False
            }
            
            return error_result
    
    def _query_ollama(self, model_name: str, prompt: str, 
                    system_prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gửi truy vấn đến Ollama API
        
        Args:
            model_name: Tên mô hình
            prompt: Truy vấn người dùng
            system_prompt: System prompt
            params: Tham số mô hình
            
        Returns:
            Dict chứa kết quả từ API
        """
        # Chuẩn bị payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "options": params
        }
        
        # Thêm system prompt nếu có
        if system_prompt:
            payload["system"] = system_prompt
            
        # Endpoint
        endpoint = f"{self.base_url}/api/generate"
        
        # Retry logic
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout khi kết nối đến Ollama (lần {attempt+1}/{self.retry_attempts})")
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Lỗi khi kết nối đến Ollama: {e}")
                raise
                
        # Không bao giờ đến đây, nhưng để đảm bảo kiểu trả về
        raise Exception("Không thể kết nối đến Ollama API sau nhiều lần thử")
    
    def _update_performance_stats(self, model_name: str, completion_time: float, 
                                token_count: int) -> None:
        """
        Cập nhật thống kê hiệu suất của mô hình
        
        Args:
            model_name: Tên mô hình
            completion_time: Thời gian hoàn thành (giây)
            token_count: Số lượng token đã xử lý
        """
        if model_name not in self.performance_stats:
            self.performance_stats[model_name] = {
                "count": 0,
                "total_time": 0,
                "total_tokens": 0,
                "avg_time": 0,
                "avg_tokens": 0,
                "tokens_per_second": 0
            }
            
        stats = self.performance_stats[model_name]
        stats["count"] += 1
        stats["total_time"] += completion_time
        stats["total_tokens"] += token_count
        
        # Cập nhật các giá trị trung bình
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["avg_tokens"] = stats["total_tokens"] / stats["count"]
        
        # Tốc độ xử lý token
        if completion_time > 0:
            stats["tokens_per_second"] = token_count / completion_time
    
    def get_performance_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Lấy thống kê hiệu suất của mô hình
        
        Args:
            model_name: Tên mô hình cụ thể (tùy chọn)
            
        Returns:
            Dict chứa thống kê hiệu suất
        """
        if model_name:
            return self.performance_stats.get(model_name, {})
        return self.performance_stats
    
    def clear_cache(self) -> None:
        """Xóa bộ đệm câu trả lời"""
        self.response_cache.clear()
        
    def reset_stats(self) -> None:
        """Đặt lại thống kê hiệu suất"""
        self.performance_stats.clear()