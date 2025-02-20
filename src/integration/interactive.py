"""
Chế độ tương tác qua CLI.
Cung cấp giao diện tương tác dòng lệnh cho hệ thống.
"""

import logging
import os
import sys
import time
from typing import Dict, Any, Optional, List, Tuple
import argparse

from src.integration.enhanced_assistant import EnhancedPersonalAssistant

logger = logging.getLogger(__name__)

class InteractiveShell:
    """Giao diện tương tác dòng lệnh cho hệ thống trợ lý."""
    
    def __init__(self, assistant: EnhancedPersonalAssistant, args: argparse.Namespace):
        """
        Khởi tạo giao diện tương tác.
        
        Args:
            assistant: Đối tượng trợ lý nâng cao
            args: Tham số dòng lệnh
        """
        self.assistant = assistant
        self.args = args
        self.running = False
        self.command_history = []
        self.special_commands = {
            'help': self.show_help,
            'exit': self.exit_shell,
            'quit': self.exit_shell,
            'thoát': self.exit_shell,
            'toggle-opt': self.toggle_optimization,
            'toggle-feedback': self.toggle_feedback,
            'toggle-auto-model': self.toggle_auto_model,
            'report': self.show_performance_report,
            'export-rlhf': self.export_rlhf_data,
            'save': self.save_conversation,
            'clear': self.clear_screen,
            'reset': self.reset_optimization,
            'status': self.show_status,
        }
        
        logger.info("Đã khởi tạo Interactive Shell")
    
    def run(self):
        """Chạy vòng lặp tương tác chính."""
        self.running = True
        self._print_welcome_message()
        
        try:
            while self.running:
                user_input = input("\nBạn: ").strip()
                
                if not user_input:
                    continue
                
                # Lưu vào lịch sử
                self.command_history.append(user_input)
                
                # Xử lý lệnh đặc biệt
                if user_input.lower() in self.special_commands:
                    self.special_commands[user_input.lower()]()
                    continue
                
                # Xử lý lệnh với tham số
                if ' ' in user_input and user_input.split()[0].lower() in self.special_commands:
                    command, *args = user_input.split(maxsplit=1)
                    if command.lower() in self.special_commands:
                        self.special_commands[command.lower()](*args)
                        continue
                
                # Xử lý câu hỏi thông thường
                self._process_query(user_input)
                
        except KeyboardInterrupt:
            print("\nĐã nhận tín hiệu thoát...")
        except EOFError:
            print("\nKết thúc đầu vào...")
        finally:
            self._handle_exit()
    
    def _process_query(self, query: str):
        """
        Xử lý câu hỏi của người dùng.
        
        Args:
            query: Câu hỏi từ người dùng
        """
        try:
            start_time = time.time()
            
            # Xử lý câu hỏi với trợ lý nâng cao
            result = self.assistant.process_query(
                query=query,
                role=self.args.role if not self.args.auto_model else None,
                temperature=self.args.temperature,
                max_tokens=self.args.max_tokens,
                group_discussion=self.args.group_discussion,
                rounds=self.args.rounds,
                collect_feedback=self.args.feedback
            )
            
            # Hiển thị kết quả
            self._display_result(result)
            
            # Hiển thị thông tin tối ưu hóa nếu có
            if "optimization_info" in result and not self.args.no_optimization:
                self._display_optimization_info(result["optimization_info"])
                
            processing_time = time.time() - start_time
            print(f"\n(Tổng thời gian xử lý: {processing_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý câu hỏi: {e}")
            print(f"\nĐã xảy ra lỗi: {str(e)}")
    
    def _display_result(self, result: Dict[str, Any]):
        """
        Hiển thị kết quả phản hồi.
        
        Args:
            result: Kết quả từ trợ lý
        """
        if "error" in result:
            print(f"\nLỗi: {result['error']}")
            return
            
        # Hiển thị kết quả thảo luận nhóm
        if self.args.group_discussion and "final_response" in result:
            print("\n" + "="*50)
            print(f"KẾT QUẢ THẢO LUẬN NHÓM")
            if "confidence_score" in result:
                print(f"(Độ tin cậy: {result['confidence_score']:.2f})")
            print("="*50)
            
            if "summary" in result and result["summary"]:
                print("\nTÓM TẮT CHÍNH:")
                print(result['summary'])
            
            print("\nPHẢN HỒI ĐẦY ĐỦ:")
            print(result['final_response'])
            
            if self.args.verbose and "discussion_log" in result:
                self._display_discussion_details(result["discussion_log"])
                
        # Hiển thị kết quả mô hình đơn
        elif "response" in result:
            print(f"\n[{result['role']} - {result['model']}]")
            print(f"Trợ lý: {result['response']}")
            
        # Hiển thị nhiều kết quả từ các mô hình khác nhau
        elif "responses" in result:
            for role, data in result["responses"].items():
                print(f"\n[{role} - {data['model']}]")
                print(f"Trợ lý: {data['response']}")
                print("-" * 40)
    
    def _display_discussion_details(self, discussion_log: List[Dict[str, Any]]):
        """
        Hiển thị chi tiết quá trình thảo luận.
        
        Args:
            discussion_log: Nhật ký quá trình thảo luận
        """
        print("\n" + "="*50)
        print("CHI TIẾT QUÁ TRÌNH THẢO LUẬN:")
        
        for round_data in discussion_log:
            round_num = round_data.get('round', 0)
            print(f"\n--- VÒNG {round_num} ---")
            
            for role, response_data in round_data.get('responses', {}).items():
                model = response_data.get('model', 'unknown')
                response = response_data.get('response', '')
                
                print(f"\n[{role} - {model}]")
                # Cắt phản hồi dài
                preview = response[:300] + "..." if len(response) > 300 else response
                print(preview)
    
    def _display_optimization_info(self, optimization_info: Dict[str, Any]):
        """
        Hiển thị thông tin tối ưu hóa.
        
        Args:
            optimization_info: Thông tin tối ưu hóa từ quá trình xử lý
        """
        if not optimization_info.get("optimization_applied", False):
            return
            
        print("\n[Thông tin tối ưu hóa]")
        
        if "suggested_model" in optimization_info:
            print(f"* Mô hình được đề xuất: {optimization_info['suggested_model']}")
            
        if "should_use_group_discussion" in optimization_info:
            use_group = "Có" if optimization_info["should_use_group_discussion"] else "Không"
            print(f"* Nên sử dụng thảo luận nhóm: {use_group}")
            
        if "top_models" in optimization_info:
            top_models = optimization_info["top_models"]
            if top_models:
                print("* Mô hình phù hợp nhất:")
                for model, score in top_models:
                    print(f"  - {model}: {score:.2f}")
    
    def _print_welcome_message(self):
        """Hiển thị thông báo chào mừng."""
        print("\n" + "="*70)
        print("  HỆ THỐNG TRỢ LÝ CÁ NHÂN NÂNG CAO VỚI RLHF VÀ DPO")
        print("="*70)
        
        # Hiển thị trạng thái
        states = []
        states.append(f"Tối ưu hóa: {'BẬT' if not self.args.no_optimization else 'TẮT'}")
        states.append(f"Thu thập phản hồi: {'BẬT' if self.args.feedback else 'TẮT'}")
        states.append(f"Tự động chọn mô hình: {'BẬT' if self.args.auto_model else 'TẮT'}")
        states.append(f"Thảo luận nhóm: {'BẬT' if self.args.group_discussion else 'TẮT'}")
        
        print(f"\nTrạng thái: {' | '.join(states)}")
        print("\nNhập 'help' để xem danh sách lệnh, 'exit' để thoát")
    
    def show_help(self):
        """Hiển thị trợ giúp về các lệnh đặc biệt."""
        print("\n" + "="*50)
        print("CÁC LỆNH ĐẶC BIỆT:")
        print("="*50)
        
        commands = [
            ("help", "Hiển thị trợ giúp này"),
            ("exit/quit/thoát", "Thoát chương trình"),
            ("toggle-opt", "Bật/tắt tối ưu hóa tự động"),
            ("toggle-feedback", "Bật/tắt thu thập phản hồi"),
            ("toggle-auto-model", "Bật/tắt tự động chọn mô hình"),
            ("report", "Hiển thị báo cáo hiệu suất mô hình"),
            ("export-rlhf [thư_mục]", "Xuất dữ liệu RLHF"),
            ("save [tên_file]", "Lưu lịch sử hội thoại"),
            ("clear", "Xóa màn hình"),
            ("reset", "Đặt lại trọng số tối ưu hóa"),
            ("status", "Hiển thị trạng thái hệ thống"),
        ]
        
        col_width = max(len(cmd[0]) for cmd in commands) + 2
        for cmd, desc in commands:
            print(f"  {cmd:<{col_width}} - {desc}")
    
    def exit_shell(self):
        """Thoát khỏi shell tương tác."""
        self.running = False
    
    def _handle_exit(self):
        """Xử lý khi thoát chương trình."""
        # Tự động lưu hội thoại nếu được cấu hình
        if self.args.save:
            self.save_conversation(self.args.save)
        else:
            # Lưu với tên file mặc định
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
            self.save_conversation(filename)
        
        print("\nCảm ơn bạn đã sử dụng hệ thống trợ lý cá nhân. Tạm biệt!")
    
    def toggle_optimization(self):
        """Bật/tắt tối ưu hóa tự động."""
        self.args.no_optimization = not self.args.no_optimization
        self.assistant.toggle_optimization(not self.args.no_optimization)
        state = "TẮT" if self.args.no_optimization else "BẬT"
        print(f"Tối ưu hóa tự động: {state}")
    
    def toggle_feedback(self):
        """Bật/tắt thu thập phản hồi."""
        self.args.feedback = not self.args.feedback
        self.assistant.toggle_feedback_collection(self.args.feedback)
        state = "BẬT" if self.args.feedback else "TẮT"
        print(f"Thu thập phản hồi: {state}")
    
    def toggle_auto_model(self):
        """Bật/tắt tự động chọn mô hình."""
        self.args.auto_model = not self.args.auto_model
        self.assistant.toggle_auto_select_model(self.args.auto_model)
        if self.args.auto_model:
            # Khi bật tự động chọn mô hình, vô hiệu hóa lựa chọn mô hình thủ công
            self.args.role = None
        state = "BẬT" if self.args.auto_model else "TẮT"
        print(f"Tự động chọn mô hình: {state}")
    
    def show_performance_report(self):
        """Hiển thị báo cáo hiệu suất mô hình."""
        from src.cli.reporting import display_performance_report
        
        try:
            report = self.assistant.get_performance_report()
            display_performance_report(report)
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị báo cáo hiệu suất: {e}")
            print(f"Không thể hiển thị báo cáo: {str(e)}")
    
    def export_rlhf_data(self, export_dir: Optional[str] = None):
        """
        Xuất dữ liệu RLHF đã thu thập.
        
        Args:
            export_dir: Thư mục đích (tùy chọn)
        """
        try:
            output_file = self.assistant.export_rlhf_dataset()
            print(f"Đã xuất dữ liệu RLHF thành công vào: {output_file}")
        except Exception as e:
            logger.error(f"Lỗi khi xuất dữ liệu RLHF: {e}")
            print(f"Không thể xuất dữ liệu RLHF: {str(e)}")
    
    def save_conversation(self, filename: Optional[str] = None):
        """
        Lưu lịch sử hội thoại.
        
        Args:
            filename: Tên file (tùy chọn)
        """
        try:
            saved_path = self.assistant.save_conversation(filename)
            print(f"Đã lưu lịch sử hội thoại vào: {saved_path}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu hội thoại: {e}")
            print(f"Không thể lưu lịch sử hội thoại: {str(e)}")
    
    def clear_screen(self):
        """Xóa màn hình console."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def reset_optimization(self):
        """Đặt lại quá trình tối ưu hóa."""
        try:
            confirm = input("Bạn có chắc chắn muốn đặt lại trọng số tối ưu hóa về mặc định? (y/n): ")
            if confirm.lower() in ['y', 'yes']:
                self.assistant.feedback_manager.reset_optimization(reset_feedback_db=False)
                print("Đã đặt lại trọng số tối ưu hóa về giá trị mặc định.")
        except Exception as e:
            logger.error(f"Lỗi khi đặt lại tối ưu hóa: {e}")
            print(f"Không thể đặt lại tối ưu hóa: {str(e)}")
    
    def show_status(self):
        """Hiển thị trạng thái hiện tại của hệ thống."""
        try:
            status = self.assistant.get_optimization_status()
            
            print("\n" + "="*50)
            print("TRẠNG THÁI HỆ THỐNG")
            print("="*50)
            
            print(f"\nCấu hình chung:")
            print(f"  Tối ưu hóa tự động: {'BẬT' if status['auto_optimization'] else 'TẮT'}")
            print(f"  Tự động chọn mô hình: {'BẬT' if status['auto_select_model'] else 'TẮT'}")
            print(f"  Thu thập phản hồi: {'BẬT' if status['feedback_enabled'] else 'TẮT'}")
            
            # Hiển thị thống kê
            if "optimization_stats" in status:
                stats = status["optimization_stats"]
                
                print(f"\nThống kê:")
                print(f"  Tổng số phản hồi: {stats.get('total_feedback_count', 0)}")
                print(f"  Số lượng mô hình: {stats.get('model_count', 0)}")
                
                # Hiển thị trọng số hiện tại
                if "current_weights" in stats:
                    print("\nTrọng số hiện tại:")
                    for model, weight in stats["current_weights"].items():
                        print(f"  {model}: {weight:.3f}")
                
                # Hiển thị số lượng phản hồi theo mô hình
                if "feedback_counts_by_model" in stats:
                    print("\nSố lượng phản hồi theo mô hình:")
                    for model, count in stats["feedback_counts_by_model"].items():
                        print(f"  {model}: {count}")
                
            print("\nSử dụng 'report' để xem báo cáo hiệu suất chi tiết")
            
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị trạng thái: {e}")
            print(f"Không thể hiển thị trạng thái: {str(e)}")


def run_interactive_mode(assistant: EnhancedPersonalAssistant, args: argparse.Namespace):
    """
    Chạy trợ lý ở chế độ tương tác.
    
    Args:
        assistant: Đối tượng trợ lý nâng cao
        args: Tham số dòng lệnh
    """
    shell = InteractiveShell(assistant, args)
    shell.run()