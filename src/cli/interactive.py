"""
CLI tương tác cho hệ thống trợ lý cá nhân
"""

import os
import sys
import cmd
import time
import logging
import json
from typing import Dict, List, Any, Optional, Tuple

from src.integration.enhanced_assistant import EnhancedPersonalAssistant

logger = logging.getLogger(__name__)

class InteractiveShell(cmd.Cmd):
    """
    Shell tương tác cho hệ thống trợ lý cá nhân
    """
    
    intro = """
======================================================================
  HỆ THỐNG TRỢ LÝ CÁ NHÂN NÂNG CAO VỚI RLHF VÀ DPO
======================================================================

Nhập 'help' để xem danh sách lệnh, 'exit' để thoát
"""
    prompt = "\nBạn: "
    
    def __init__(self, assistant: EnhancedPersonalAssistant, model_name: Optional[str] = None):
        """
        Khởi tạo Interactive Shell
        
        Args:
            assistant: Đối tượng EnhancedPersonalAssistant
            model_name: Mô hình mặc định (tùy chọn)
        """
        super().__init__()
        self.assistant = assistant
        self.model_name = model_name
        self.conversation_id = None
        self.user_info = None
        self.system_prompt = None
        self.last_query = None
        
        # Cập nhật trạng thái hiển thị
        self._update_status_display()
        
        logger.info("Đã khởi tạo Interactive Shell")
        
    def _update_status_display(self) -> None:
        """Cập nhật trạng thái hiển thị"""
        optimization = "BẬT" if self.assistant.optimization_enabled else "TẮT"
        feedback = "BẬT" if self.assistant.feedback_collection_enabled else "TẮT"
        auto_model = "BẬT" if self.assistant.auto_select_model else "TẮT"
        group_discussion = "BẬT" if self.assistant.use_group_discussion else "TẮT"
        
        status_info = f"Tối ưu hóa: {optimization} | Thu thập phản hồi: {feedback} | Tự động chọn mô hình: {auto_model} | Thảo luận nhóm: {group_discussion}"
        
        if self.model_name:
            status_info += f" | Mô hình: {self.model_name}"
            
        self.status = status_info
    
    def preloop(self) -> None:
        """Thiết lập trước khi vào vòng lặp chính"""
        # Khởi tạo cuộc hội thoại mới
        self.conversation_id = f"conv_{int(time.time())}"
    
    def default(self, line: str) -> bool:
        """
        Xử lý đầu vào không khớp với lệnh
        
        Args:
            line: Dòng đầu vào
            
        Returns:
            False để tiếp tục vòng lặp
        """
        if line.strip():
            self._process_query(line.strip())
        return False
    
    def emptyline(self) -> bool:
        """
        Xử lý khi người dùng nhập dòng trống
        
        Returns:
            False để tiếp tục vòng lặp
        """
        return False
    
    def _process_query(self, query: str) -> None:
        """
        Xử lý truy vấn của người dùng
        
        Args:
            query: Truy vấn của người dùng
        """
        self.last_query = query
        start_time = time.time()
        
        try:
            result = self.assistant.get_response(
                query=query,
                conversation_id=self.conversation_id,
                user_info=self.user_info,
                model_name=self.model_name,
                system_prompt=self.system_prompt
            )
            
            response_text = result.get("response", "")
            model_used = result.get("model_used", "")
            completion_time = result.get("completion_time", 0)
            
            # Hiển thị câu trả lời
            print(f"\nTrợ lý ({model_used}, {completion_time:.2f}s): {response_text}")
            
            # Kiểm tra xem có nên yêu cầu phản hồi hay không
            self._maybe_ask_for_feedback()
            
        except KeyboardInterrupt:
            print("\nĐã hủy yêu cầu.")
        except Exception as e:
            logger.error(f"Lỗi khi xử lý truy vấn: {e}")
            print(f"\nXảy ra lỗi: {e}")
            
        # Hiển thị tổng thời gian
        total_time = time.time() - start_time
        if total_time > 0.5:  # Chỉ hiển thị nếu mất nhiều thời gian
            print(f"(Hoàn thành trong {total_time:.2f}s)")
    
    def _maybe_ask_for_feedback(self) -> None:
        """Yêu cầu phản hồi từ người dùng nếu đủ điều kiện"""
        if not self.assistant.feedback_collection_enabled:
            return
            
        # Xác định có yêu cầu phản hồi hay không (logic từ FeedbackCollector)
        try:
            should_ask = self.assistant.feedback_manager.feedback_collector.should_request_feedback(
                self.conversation_id)
        except AttributeError:
            # Nếu không có phương thức should_request_feedback, sử dụng xác suất ngẫu nhiên
            import random
            should_ask = random.random() < 0.3
            
        if should_ask:
            try:
                print("\n--- Phản hồi ---")
                print("Bạn đánh giá câu trả lời này như thế nào? (1-5, hoặc bỏ qua)")
                rating = input("Đánh giá: ").strip()
                
                if rating and rating in "12345":
                    score = float(rating) / 5.0
                    
                    print("Bạn có thêm nhận xét gì không? (nhấn Enter để bỏ qua)")
                    feedback_text = input("Nhận xét: ").strip()
                    
                    # Lấy câu trả lời cuối cùng
                    history = self.assistant.get_conversation_history()
                    if history and len(history) >= 2:
                        last_response = history[-1].get("content", "")
                        
                        # Lưu phản hồi
                        self.assistant.provide_feedback(
                            query=self.last_query,
                            selected_response=last_response,
                            feedback_score=score,
                            feedback_text=feedback_text if feedback_text else None
                        )
                        
                        print("Cảm ơn phản hồi của bạn!")
                    
            except KeyboardInterrupt:
                print("\nĐã bỏ qua phản hồi.")
            except Exception as e:
                logger.error(f"Lỗi khi thu thập phản hồi: {e}")
    
    def do_exit(self, arg: str) -> bool:
        """
        Thoát khỏi shell tương tác
        
        Args:
            arg: Tham số (không sử dụng)
            
        Returns:
            True để kết thúc vòng lặp
        """
        print("Tạm biệt!")
        return True
        
    def do_quit(self, arg: str) -> bool:
        """Alias cho exit"""
        return self.do_exit(arg)
        
    def do_bye(self, arg: str) -> bool:
        """Alias cho exit"""
        return self.do_exit(arg)
    
    def do_clear(self, arg: str) -> None:
        """
        Xóa màn hình và khởi tạo cuộc hội thoại mới
        
        Args:
            arg: Tham số (không sử dụng)
        """
        # Xóa màn hình
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Khởi tạo cuộc hội thoại mới
        self.assistant.clear_conversation()
        self.conversation_id = f"conv_{int(time.time())}"
        
        # Hiển thị lại giới thiệu
        print(self.intro)
        self._update_status_display()
        print(f"Trạng thái: {self.status}")
        
        print("Đã xóa hội thoại và bắt đầu cuộc hội thoại mới.")
    
    def do_status(self, arg: str) -> None:
        """
        Hiển thị trạng thái hiện tại
        
        Args:
            arg: Tham số (không sử dụng)
        """
        self._update_status_display()
        print(f"Trạng thái: {self.status}")
        
        # Hiển thị thông tin chi tiết
        stats = self.assistant.get_stats()
        optimization = stats.get("optimization", {})
        
        print("\nThông tin chi tiết:")
        print(f"- Cuộc hội thoại hiện tại: {self.conversation_id}")
        print(f"- Số câu trả lời đã thu thập: {optimization.get('feedback_collection', {}).get('total_samples', 0)}")
        
        if self.model_name:
            print(f"- Mô hình đang sử dụng: {self.model_name}")
        
        # Hiển thị trọng số mô hình nếu có
        model_weights = optimization.get("model_weights", {})
        if model_weights:
            print("\nTrọng số mô hình:")
            for model, weight in model_weights.items():
                print(f"- {model}: {weight:.2f}")
    
    def do_model(self, arg: str) -> None:
        """
        Đặt hoặc hiển thị mô hình hiện tại
        
        Args:
            arg: Tên mô hình cần đặt
        """
        if not arg:
            available_models = []
            try:
                available_models = self.assistant.model_manager.list_models()
            except:
                # Lấy danh sách mô hình thông qua EnhancedPersonalAssistant
                pass
                
            print(f"Mô hình hiện tại: {self.model_name or 'auto'}")
            if available_models:
                print(f"Các mô hình khả dụng: {', '.join(available_models)}")
            return
            
        arg = arg.strip()
        if arg == "auto":
            self.model_name = None
            self.assistant.toggle_auto_select_model(True)
            print("Đã chuyển sang chế độ tự động chọn mô hình.")
        else:
            available_models = []
            try:
                available_models = self.assistant.model_manager.list_models()
            except:
                # Thử cách khác để lấy danh sách mô hình
                try:
                    available_models = [m.get("name") for m in self.assistant.config.get("models", [])]
                except:
                    pass
                    
            if arg in available_models:
                self.model_name = arg
                print(f"Đã chuyển sang sử dụng mô hình: {arg}")
            else:
                print(f"Lỗi: Mô hình '{arg}' không tồn tại.")
                if available_models:
                    print(f"Các mô hình khả dụng: {', '.join(available_models)}")
                
        self._update_status_display()
    
    def do_toggle(self, arg: str) -> None:
        """
        Bật/tắt các tính năng
        
        Args:
            arg: Tên tính năng (optimization, feedback, auto-model, group-discussion)
        """
        valid_features = ["optimization", "feedback", "auto-model", "group-discussion"]
        
        if not arg or arg.strip() not in valid_features:
            print(f"Cú pháp: toggle <tính năng>")
            print(f"Các tính năng: {', '.join(valid_features)}")
            return
            
        feature = arg.strip()
        
        if feature == "optimization":
            new_state = not self.assistant.optimization_enabled
            self.assistant.toggle_optimization(new_state)
            print(f"Tối ưu hóa: {'BẬT' if new_state else 'TẮT'}")
            
        elif feature == "feedback":
            new_state = not self.assistant.feedback_collection_enabled
            self.assistant.toggle_feedback_collection(new_state)
            print(f"Thu thập phản hồi: {'BẬT' if new_state else 'TẮT'}")
            
        elif feature == "auto-model":
            new_state = not self.assistant.auto_select_model
            self.assistant.toggle_auto_select_model(new_state)
            print(f"Tự động chọn mô hình: {'BẬT' if new_state else 'TẮT'}")
            
        elif feature == "group-discussion":
            new_state = not self.assistant.use_group_discussion
            self.assistant.toggle_group_discussion(new_state)
            print(f"Thảo luận nhóm: {'BẬT' if new_state else 'TẮT'}")
            
        self._update_status_display()
    
    def do_system(self, arg: str) -> None:
        """
        Đặt hoặc hiển thị system prompt
        
        Args:
            arg: System prompt mới
        """
        if not arg:
            print(f"System prompt hiện tại: {self.system_prompt or 'Mặc định'}")
            return
            
        self.system_prompt = arg.strip()
        print(f"Đã đặt system prompt mới.")
    
    def do_user(self, arg: str) -> None:
        """
        Đặt thông tin người dùng
        
        Args:
            arg: Thông tin người dùng dạng JSON
        """
        if not arg:
            print(f"Thông tin người dùng hiện tại: {json.dumps(self.user_info, ensure_ascii=False) if self.user_info else 'Không có'}")
            return
            
        try:
            self.user_info = json.loads(arg.strip())
            print(f"Đã đặt thông tin người dùng mới.")
        except json.JSONDecodeError:
            print("Lỗi: Thông tin không đúng định dạng JSON.")
    
    def do_export(self, arg: str) -> None:
        """
        Xuất dữ liệu phản hồi
        
        Args:
            arg: Thư mục xuất (tùy chọn)
        """
        export_dir = arg.strip() if arg else None
        
        try:
            export_path = self.assistant.export_feedback_data(export_dir)
            if export_path:
                print(f"Đã xuất dữ liệu phản hồi đến: {export_path}")
            else:
                print("Không thể xuất dữ liệu phản hồi.")
        except Exception as e:
            print(f"Lỗi khi xuất dữ liệu: {e}")
    
    def do_help(self, arg: str) -> None:
        """
        Hiển thị trợ giúp
        
        Args:
            arg: Tên lệnh cần trợ giúp
        """
        if not arg:
            print("\nCác lệnh có sẵn:")
            print("  status        - Hiển thị trạng thái hiện tại")
            print("  model [name]  - Đặt hoặc hiển thị mô hình ('auto' để tự động)")
            print("  toggle <opt>  - Bật/tắt tính năng (optimization, feedback, auto-model, group-discussion)")
            print("  system [text] - Đặt hoặc hiển thị system prompt")
            print("  user [json]   - Đặt hoặc hiển thị thông tin người dùng")
            print("  export [dir]  - Xuất dữ liệu phản hồi")
            print("  clear         - Xóa màn hình và bắt đầu cuộc hội thoại mới")
            print("  exit/quit     - Thoát chương trình")
            print("\nGõ trực tiếp câu hỏi để tương tác với trợ lý.")
            return
            
        super().do_help(arg)
    
    def run(self) -> None:
        """Chạy shell tương tác"""
        self._update_status_display()
        print(f"Trạng thái: {self.status}")
        
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\nĐã nhận tín hiệu ngắt, thoát...")
        except Exception as e:
            logger.error(f"Lỗi không mong đợi trong shell: {e}")
            print(f"\nXảy ra lỗi: {e}")
        finally:
            print("Tạm biệt!")