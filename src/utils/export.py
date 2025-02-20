"""
Xuất dữ liệu từ hệ thống.
Cung cấp các tiện ích để xuất dữ liệu phản hồi, báo cáo, và lịch sử hội thoại.
"""

import os
import json
import logging
import csv
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

def export_rlhf_data(rlhf_data: Dict[str, Any], export_dir: str) -> str:
    """
    Xuất dữ liệu RLHF ra file.
    
    Args:
        rlhf_data: Dữ liệu RLHF
        export_dir: Thư mục xuất
        
    Returns:
        Đường dẫn đến file đã xuất
    """
    # Đảm bảo thư mục xuất tồn tại
    os.makedirs(export_dir, exist_ok=True)
    
    # Tạo tên file với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(export_dir, f"rlhf_dataset_{timestamp}.json")
    
    # Thêm metadata xuất
    rlhf_data["export_metadata"] = {
        "exported_at": datetime.now().isoformat(),
        "format_version": "1.0.0",
        "export_tool": "personal_assistant_rlhf"
    }
    
    # Ghi dữ liệu vào file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rlhf_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Đã xuất {len(rlhf_data.get('scalar_feedback', []))} phản hồi và "
               f"{len(rlhf_data.get('preference_pairs', []))} cặp ưu tiên vào {output_file}")
    
    # Tạo file CSV cho dễ phân tích
    _export_rlhf_csv(rlhf_data, export_dir, timestamp)
    
    return output_file

def _export_rlhf_csv(rlhf_data: Dict[str, Any], export_dir: str, timestamp: str) -> None:
    """
    Xuất dữ liệu RLHF ra file CSV.
    
    Args:
        rlhf_data: Dữ liệu RLHF
        export_dir: Thư mục xuất
        timestamp: Mốc thời gian cho tên file
    """
    # Xuất phản hồi có điểm số
    scalar_file = os.path.join(export_dir, f"rlhf_scalar_feedback_{timestamp}.csv")
    scalar_feedback = rlhf_data.get("scalar_feedback", [])
    
    if scalar_feedback:
        with open(scalar_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["query", "model", "score", "feedback", "response_preview"])
            
            # Data
            for item in scalar_feedback:
                query = item.get("query", "")
                model = item.get("model", "")
                score = item.get("score", "")
                feedback = item.get("feedback", "")
                response = item.get("response", "")
                # Cắt phản hồi dài
                response_preview = response[:100] + "..." if len(response) > 100 else response
                # Loại bỏ ký tự xuống dòng
                response_preview = response_preview.replace("\n", " ")
                
                writer.writerow([query, model, score, feedback, response_preview])
        
        logger.info(f"Đã xuất {len(scalar_feedback)} phản hồi ra {scalar_file}")
    
    # Xuất cặp ưu tiên
    preference_file = os.path.join(export_dir, f"rlhf_preference_pairs_{timestamp}.csv")
    preference_pairs = rlhf_data.get("preference_pairs", [])
    
    if preference_pairs:
        with open(preference_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["query", "chosen_model", "rejected_model"])
            
            # Data
            for item in preference_pairs:
                query = item.get("query", "")
                chosen_model = item.get("chosen", {}).get("model", "")
                rejected_model = item.get("rejected", {}).get("model", "")
                
                writer.writerow([query, chosen_model, rejected_model])
        
        logger.info(f"Đã xuất {len(preference_pairs)} cặp ưu tiên ra {preference_file}")

def export_performance_report(report: Dict[str, Any], export_dir: str) -> Dict[str, str]:
    """
    Xuất báo cáo hiệu suất ra các file.
    
    Args:
        report: Dữ liệu báo cáo hiệu suất
        export_dir: Thư mục xuất
        
    Returns:
        Dict chứa đường dẫn đến các file đã xuất
    """
    # Đảm bảo thư mục xuất tồn tại
    os.makedirs(export_dir, exist_ok=True)
    
    # Tạo tên file với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exported_files = {}
    
    # Xuất dữ liệu JSON đầy đủ
    json_file = os.path.join(export_dir, f"performance_report_{timestamp}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    exported_files["json"] = json_file
    
    # Xuất metrics dạng CSV
    if "model_metrics" in report:
        metrics_file = os.path.join(export_dir, f"model_metrics_{timestamp}.csv")
        with open(metrics_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["model", "avg_score", "win_rate", "sample_count", "last_updated"])
            
            # Data
            for model, metrics in report["model_metrics"].items():
                writer.writerow([
                    model,
                    metrics.get("avg_score", 0),
                    metrics.get("win_rate", 0),
                    metrics.get("sample_count", 0),
                    metrics.get("last_updated", "")
                ])
        exported_files["metrics_csv"] = metrics_file
    
    # Xuất xu hướng hiệu suất dạng CSV
    if "performance_trends" in report:
        trends_file = os.path.join(export_dir, f"performance_trends_{timestamp}.csv")
        with open(trends_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["model", "date", "avg_score", "sample_count"])
            
            # Data
            for model, trend in report["performance_trends"].items():
                for entry in trend:
                    writer.writerow([
                        model,
                        entry.get("date", ""),
                        entry.get("avg_score", 0),
                        entry.get("sample_count", 0)
                    ])
        exported_files["trends_csv"] = trends_file
    
    # Tạo báo cáo HTML đơn giản
    html_file = os.path.join(export_dir, f"performance_report_{timestamp}.html")
    _generate_html_report(report, html_file)
    exported_files["html"] = html_file
    
    logger.info(f"Đã xuất báo cáo hiệu suất ra {len(exported_files)} file trong {export_dir}")
    return exported_files

def _generate_html_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Tạo báo cáo HTML đơn giản từ dữ liệu.
    
    Args:
        report: Dữ liệu báo cáo
        output_path: Đường dẫn file đầu ra
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Báo cáo hiệu suất mô hình</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            h2 {{ color: #3498db; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .info {{ background-color: #e7f4ff; padding: 10px; border-radius: 5px; }}
            .timestamp {{ color: #7f8c8d; font-style: italic; text-align: center; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Báo cáo hiệu suất mô hình</h1>
            <p class="info">Báo cáo này được tạo tự động từ dữ liệu phản hồi người dùng.</p>
            
            <h2>Hiệu suất mô hình</h2>
            <table>
                <tr>
                    <th>Mô hình</th>
                    <th>Điểm trung bình</th>
                    <th>Tỷ lệ thắng</th>
                    <th>Số mẫu</th>
                    <th>Cập nhật gần nhất</th>
                </tr>
    """
    
    # Thêm dữ liệu metrics
    for model, metrics in report.get("model_metrics", {}).items():
        html_content += f"""
                <tr>
                    <td>{model}</td>
                    <td>{metrics.get("avg_score", 0):.2f}</td>
                    <td>{metrics.get("win_rate", 0):.2f}</td>
                    <td>{metrics.get("sample_count", 0)}</td>
                    <td>{metrics.get("last_updated", "N/A")}</td>
                </tr>
        """
    
    html_content += """
            </table>
            
            <h2>Số lần được chọn</h2>
            <table>
                <tr>
                    <th>Mô hình</th>
                    <th>Số lần được chọn</th>
                </tr>
    """
    
    # Thêm dữ liệu preference stats
    for model, count in report.get("preference_stats", {}).items():
        html_content += f"""
                <tr>
                    <td>{model}</td>
                    <td>{count}</td>
                </tr>
        """
    
    html_content += """
            </table>
            
            <h2>Trọng số ưu tiên hiện tại</h2>
            <table>
                <tr>
                    <th>Mô hình</th>
                    <th>Trọng số</th>
                </tr>
    """
    
    # Thêm dữ liệu preference weights
    for model, weight in report.get("preference_weights", {}).items():
        html_content += f"""
                <tr>
                    <td>{model}</td>
                    <td>{weight:.2f}</td>
                </tr>
        """
    
    # Thêm thời gian tạo báo cáo
    generated_at = report.get("generated_at", datetime.now().isoformat())
    
    html_content += f"""
            </table>
            
            <p class="timestamp">Báo cáo được tạo vào: {generated_at}</p>
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def export_conversation_history(conversation_data: Dict[str, Any], export_dir: str, formats: List[str] = ["json", "txt"]) -> Dict[str, str]:
    """
    Xuất lịch sử hội thoại ra nhiều định dạng.
    
    Args:
        conversation_data: Dữ liệu hội thoại
        export_dir: Thư mục xuất
        formats: Các định dạng cần xuất
        
    Returns:
        Dict chứa đường dẫn đến các file đã xuất
    """
    # Đảm bảo thư mục xuất tồn tại
    os.makedirs(export_dir, exist_ok=True)
    
    # Tạo tên file với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exported_files = {}
    
    # Xuất theo từng định dạng yêu cầu
    if "json" in formats:
        json_file = os.path.join(export_dir, f"conversation_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        exported_files["json"] = json_file
    
    if "txt" in formats:
        txt_file = os.path.join(export_dir, f"conversation_{timestamp}.txt")
        _export_conversation_as_text(conversation_data, txt_file)
        exported_files["txt"] = txt_file
    
    if "html" in formats:
        html_file = os.path.join(export_dir, f"conversation_{timestamp}.html")
        _export_conversation_as_html(conversation_data, html_file)
        exported_files["html"] = html_file
    
    if "csv" in formats:
        csv_file = os.path.join(export_dir, f"conversation_{timestamp}.csv")
        _export_conversation_as_csv(conversation_data, csv_file)
        exported_files["csv"] = csv_file
    
    logger.info(f"Đã xuất lịch sử hội thoại ra {len(exported_files)} file trong {export_dir}")
    return exported_files

def _export_conversation_as_text(conversation_data: Dict[str, Any], output_path: str) -> None:
    """
    Xuất hội thoại dạng văn bản thuần túy.
    
    Args:
        conversation_data: Dữ liệu hội thoại
        output_path: Đường dẫn file đầu ra
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Viết thông tin tóm tắt
        f.write("LỊCH SỬ HỘI THOẠI\n")
        f.write("=" * 80 + "\n\n")
        
        metadata = conversation_data.get("metadata", {})
        f.write(f"Tạo vào: {metadata.get('created_at', 'N/A')}\n")
        f.write(f"Số lượng tin nhắn: {metadata.get('message_count', 0)}\n")
        f.write(f"Phiên bản: {metadata.get('version', 'N/A')}\n\n")
        f.write("=" * 80 + "\n\n")
        
        # Viết nội dung hội thoại
        for message in conversation_data.get("history", []):
            role = message.get("role", "unknown")
            model = message.get("model", "")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            if timestamp and len(timestamp) > 19:
                timestamp = timestamp[:19]
                
            # Định dạng tin nhắn
            if role == "user":
                f.write(f"Người dùng ({timestamp}):\n")
            else:
                f.write(f"Trợ lý [{model}] ({timestamp}):\n")
                
            f.write(f"{content}\n\n")
            f.write("-" * 80 + "\n\n")

def _export_conversation_as_csv(conversation_data: Dict[str, Any], output_path: str) -> None:
    """
    Xuất hội thoại dạng CSV.
    
    Args:
        conversation_data: Dữ liệu hội thoại
        output_path: Đường dẫn file đầu ra
    """
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["timestamp", "role", "model", "content_preview", "content_length"])
        
        # Data
        for message in conversation_data.get("history", []):
            timestamp = message.get("timestamp", "")
            role = message.get("role", "unknown")
            model = message.get("model", "")
            content = message.get("content", "")
            
            # Cắt nội dung dài và loại bỏ xuống dòng
            content_preview = content.replace("\n", " ")
            if len(content_preview) > 100:
                content_preview = content_preview[:97] + "..."
                
            writer.writerow([
                timestamp,
                role,
                model,
                content_preview,
                len(content)
            ])

def _export_conversation_as_html(conversation_data: Dict[str, Any], output_path: str) -> None:
    """
    Xuất hội thoại dạng HTML.
    
    Args:
        conversation_data: Dữ liệu hội thoại
        output_path: Đường dẫn file đầu ra
    """
    metadata = conversation_data.get("metadata", {})
    created_at = metadata.get("created_at", "N/A")
    message_count = metadata.get("message_count", 0)
    version = metadata.get("version", "N/A")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lịch sử hội thoại</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .metadata {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 30px; }}
            .message {{ margin-bottom: 20px; padding: 15px; border-radius: 10px; }}
            .user {{ background-color: #e7f4ff; text-align: right; margin-left: 50px; }}
            .assistant {{ background-color: #f0f0f0; margin-right: 50px; }}
            .header {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
            .timestamp {{ color: #7f8c8d; font-size: 0.8em; }}
            .model {{ font-weight: bold; color: #16a085; }}
            .content {{ white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lịch sử hội thoại</h1>
            
            <div class="metadata">
                <p><strong>Tạo vào:</strong> {created_at}</p>
                <p><strong>Số lượng tin nhắn:</strong> {message_count}</p>
                <p><strong>Phiên bản:</strong> {version}</p>
            </div>
    """
    
    # Thêm tin nhắn
    for message in conversation_data.get("history", []):
        role = message.get("role", "unknown")
        model = message.get("model", "")
        content = message.get("content", "").replace("\n", "<br>")
        timestamp = message.get("timestamp", "")
        
        if timestamp and len(timestamp) > 19:
            timestamp = timestamp[:19]
            
        css_class = "user" if role == "user" else "assistant"
        
        html_content += f"""
            <div class="message {css_class}">
                <div class="header">
                    <span class="role">{role.capitalize()}</span>
        """
        
        if role != "user" and model:
            html_content += f'<span class="model">[{model}]</span>'
            
        html_content += f"""
                    <span class="timestamp">{timestamp}</span>
                </div>
                <div class="content">{content}</div>
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def create_backup(source_path: str, backup_dir: Optional[str] = None) -> str:
    """
    Tạo bản sao lưu của một file.
    
    Args:
        source_path: Đường dẫn đến file nguồn
        backup_dir: Thư mục lưu bản sao (mặc định là thư mục chứa file nguồn + /backups)
        
    Returns:
        Đường dẫn đến file bản sao
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {source_path}")
        
    # Xác định thư mục backup
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(source_path), "backups")
        
    os.makedirs(backup_dir, exist_ok=True)
    
    # Tạo tên file backup
    filename = os.path.basename(source_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}.bak"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Sao chép file
    shutil.copy2(source_path, backup_path)
    logger.info(f"Đã tạo bản sao lưu tại: {backup_path}")
    
    return backup_path