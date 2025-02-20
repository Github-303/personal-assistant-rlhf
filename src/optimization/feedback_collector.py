"""
Module thu thập và quản lý phản hồi cho RLHF
"""

import os
import json
import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime

from src.optimization.feedback_store import FeedbackStore

logger = logging.getLogger(__name__)

class FeedbackCollector:
    """
    Thu thập và quản lý phản hồi người dùng để sử dụng trong RLHF
    """
    
    def __init__(self, feedback_store: FeedbackStore, config: Dict[str, Any]):
        """
        Khởi tạo Feedback Collector
        
        Args:
            feedback_store: Kho lưu trữ phản hồi
            config: Cấu hình hệ thống
        """
        self.store = feedback_store
        self.config = config
        self.feedback_config = config.get("optimization", {}).get("feedback", {})
        
        # Cấu hình thu thập
        self.enabled = self.feedback_config.get("enabled", True)
        self.collection_probability = self.feedback_config.get("collection_probability", 0.3)
        self.collect_comparisons = self.feedback_config.get("collect_comparisons", True)
        self.feedback_cache_size = self.feedback_config.get("feedback_cache_size", 1000)
        
        # Bộ nhớ cache cho phản hồi
        self.feedback_cache = {}
        
        # Danh sách các ID hội thoại đã yêu cầu phản hồi
        self.requested_feedback_conversations = set()
        
        logger.info("Đã khởi tạo RLHF Feedback Collector")
        
    def collect_feedback(self, conversation_id: str, query: str, 
                        responses: Dict[str, str], selected_response: str,
                        feedback_score: Optional[float] = None,
                        feedback_text: Optional[str] = None) -> Optional[str]:
        """
        Thu thập phản hồi về câu trả lời
        
        Args:
            conversation_id: ID của cuộc hội thoại
            query: Truy vấn người dùng
            responses: Dict các câu trả lời với key là model_name
            selected_response: Tên mô hình được chọn
            feedback_score: Điểm đánh giá (0-1, tùy chọn)
            feedback_text: Phản hồi dạng văn bản (tùy chọn)
            
        Returns:
            ID phản hồi nếu thành công, None nếu không
        """
        if not self.enabled:
            return None
            
        try:
            # Tạo bản ghi phản hồi
            feedback_record = {
                "id": f"fb_{int(time.time())}_{random.randint(1000, 9999)}",
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "query": query,
                "responses": responses,
                "selected_response": selected_response,
                "feedback_score": feedback_score,
                "feedback_text": feedback_text
            }
            
            # Lưu vào cơ sở dữ liệu
            feedback_id = self.store.save_feedback(feedback_record)
            
            # Lưu vào cache
            self._update_feedback_cache(feedback_id, feedback_record)
            
            # Nếu cần thu thập so sánh, tạo các bản ghi so sánh cặp
            if self.collect_comparisons and len(responses) > 1:
                self._create_pairwise_comparisons(
                    conversation_id, query, responses, selected_response)
                
            return feedback_id
            
        except Exception as e:
            logger.error(f"Lỗi khi thu thập phản hồi: {e}")
            return None
    
    def should_request_feedback(self, conversation_id: str) -> bool:
        """
        Xác định xem có nên yêu cầu phản hồi cho cuộc hội thoại này hay không
        
        Args:
            conversation_id: ID của cuộc hội thoại
            
        Returns:
            True nếu nên yêu cầu phản hồi, False nếu không
        """
        if not self.enabled:
            return False
            
        # Không yêu cầu phản hồi nếu đã yêu cầu cho cuộc hội thoại này
        if conversation_id in self.requested_feedback_conversations:
            return False
            
        # Yêu cầu phản hồi với xác suất được cấu hình
        should_request = random.random() < self.collection_probability
        
        if should_request:
            self.requested_feedback_conversations.add(conversation_id)
            
        return should_request
    
    def export_feedback_data(self, export_dir: str) -> str:
        """
        Xuất dữ liệu phản hồi sang định dạng JSON cho RLHF
        
        Args:
            export_dir: Thư mục đích cho dữ liệu xuất
            
        Returns:
            Đường dẫn đến file xuất
        """
        os.makedirs(export_dir, exist_ok=True)
        
        try:
            # Lấy tất cả phản hồi
            all_feedback = self.store.get_all_feedback()
            
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = os.path.join(export_dir, f"feedback_export_{timestamp}.json")
            
            # Chuyển đổi định dạng dữ liệu
            export_data = self._convert_to_rlhf_format(all_feedback)
            
            # Ghi ra file
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Đã xuất {len(all_feedback)} bản ghi phản hồi đến {export_file}")
            return export_file
            
        except Exception as e:
            logger.error(f"Lỗi khi xuất dữ liệu phản hồi: {e}")
            return ""
    
    def toggle_collection(self, enabled: bool) -> None:
        """
        Bật/tắt thu thập phản hồi
        
        Args:
            enabled: True để bật, False để tắt
        """
        self.enabled = enabled
        if enabled:
            logger.info("Đã bật thu thập phản hồi RLHF")
        else:
            logger.info("Đã tắt thu thập phản hồi RLHF")
    
    def _update_feedback_cache(self, feedback_id: str, feedback_record: Dict[str, Any]) -> None:
        """
        Cập nhật bộ nhớ cache phản hồi
        
        Args:
            feedback_id: ID của phản hồi
            feedback_record: Bản ghi phản hồi
        """
        # Thêm vào cache
        self.feedback_cache[feedback_id] = feedback_record
        
        # Giới hạn kích thước cache
        if len(self.feedback_cache) > self.feedback_cache_size:
            # Xóa các mục cũ nhất
            oldest_keys = sorted(self.feedback_cache.keys(), 
                                key=lambda k: self.feedback_cache[k].get("timestamp", ""))[:100]
            for key in oldest_keys:
                del self.feedback_cache[key]
    
    def _create_pairwise_comparisons(self, conversation_id: str, query: str,
                                    responses: Dict[str, str], selected_response: str) -> None:
        """
        Tạo các bản ghi so sánh cặp cho DPO
        
        Args:
            conversation_id: ID của cuộc hội thoại
            query: Truy vấn người dùng
            responses: Dict các câu trả lời với key là model_name
            selected_response: Tên mô hình được chọn
        """
        # Lấy câu trả lời được chọn
        chosen_text = responses.get(selected_response, "")
        if not chosen_text:
            return
            
        # Tạo các bản ghi so sánh
        for model, response in responses.items():
            if model == selected_response or not response:
                continue
                
            # Tạo bản ghi DPO với "chọn" và "từ chối"
            comparison_record = {
                "id": f"comp_{int(time.time())}_{random.randint(1000, 9999)}",
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "query": query,
                "chosen": chosen_text,
                "rejected": response,
                "chosen_model": selected_response,
                "rejected_model": model,
                "type": "pairwise_comparison"
            }
            
            # Lưu vào cơ sở dữ liệu
            self.store.save_comparison(comparison_record)
    
    def _convert_to_rlhf_format(self, feedback_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Chuyển đổi bản ghi phản hồi sang định dạng thích hợp cho RLHF
        
        Args:
            feedback_records: Danh sách các bản ghi phản hồi
            
        Returns:
            Dữ liệu đã được chuyển đổi sang định dạng RLHF
        """
        rlhf_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "record_count": len(feedback_records)
            },
            "feedback": [],
            "comparisons": []
        }
        
        # Chuyển đổi từng bản ghi
        for record in feedback_records:
            if record.get("type") == "pairwise_comparison":
                # Bản ghi so sánh
                rlhf_data["comparisons"].append({
                    "id": record.get("id"),
                    "prompt": record.get("query"),
                    "chosen": record.get("chosen"),
                    "rejected": record.get("rejected"),
                    "chosen_model": record.get("chosen_model"),
                    "rejected_model": record.get("rejected_model")
                })
            else:
                # Bản ghi phản hồi
                rlhf_record = {
                    "id": record.get("id"),
                    "prompt": record.get("query"),
                    "response": record.get("responses", {}).get(record.get("selected_response", "")),
                    "model": record.get("selected_response"),
                    "score": record.get("feedback_score"),
                    "feedback": record.get("feedback_text")
                }
                rlhf_data["feedback"].append(rlhf_record)
                
        return rlhf_data