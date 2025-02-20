"""
Báo cáo hiệu suất và phân tích dữ liệu.
Hiển thị báo cáo và thống kê từ dữ liệu thu thập được.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def display_performance_report(report: Dict[str, Any]):
    """
    Hiển thị báo cáo hiệu suất của các mô hình.
    
    Args:
        report: Dict chứa dữ liệu báo cáo hiệu suất
    """
    if "error" in report:
        print(f"\nLỗi khi tạo báo cáo: {report['error']}")
        return
        
    print("\n" + "="*70)
    print("  BÁO CÁO HIỆU SUẤT MÔ HÌNH DỰA TRÊN PHẢN HỒI NGƯỜI DÙNG")
    print("="*70)
    
    # Hiển thị metrics của mô hình
    print("\nHIỆU SUẤT MÔ HÌNH:")
    print("-" * 80)
    print(f"{'Mô hình':<20} {'Điểm TB':<10} {'Tỷ lệ thắng':<15} {'Số mẫu':<10} {'Cập nhật gần nhất':<20}")
    print("-" * 80)
    
    for model, metrics in report.get("model_metrics", {}).items():
        avg_score = metrics.get("avg_score", 0)
        win_rate = metrics.get("win_rate", 0)
        samples = metrics.get("sample_count", 0)
        last_updated = metrics.get("last_updated", "N/A")
        
        if isinstance(last_updated, str) and len(last_updated) > 19:
            last_updated = last_updated[:19]  # Cắt bớt phần mili giây
        
        print(f"{model:<20} {avg_score:<10.2f} {win_rate:<15.2f} {samples:<10} {last_updated:<20}")
    
    # Hiển thị thống kê ưu tiên
    print("\nSỐ LẦN ĐƯỢC CHỌN:")
    preference_stats = report.get("preference_stats", {})
    if preference_stats:
        for model, count in preference_stats.items():
            print(f"  {model}: {count} lần")
    else:
        print("  Chưa có dữ liệu so sánh ưu tiên.")
    
    # Hiển thị trọng số ưu tiên
    print("\nTRỌNG SỐ ƯU TIÊN HIỆN TẠI:")
    preference_weights = report.get("preference_weights", {})
    if preference_weights:
        for model, weight in preference_weights.items():
            print(f"  {model}: {weight:.2f}")
    else:
        print("  Chưa có trọng số ưu tiên.")
    
    # Hiển thị xu hướng hiệu suất
    if "performance_trends" in report and report["performance_trends"]:
        print("\nXU HƯỚNG HIỆU SUẤT (30 NGÀY QUA):")
        for model, trend in report["performance_trends"].items():
            if trend:
                print(f"\n  {model}:")
                print(f"    {'Ngày':<12} {'Điểm TB':<10} {'Số mẫu':<8}")
                print(f"    {'-'*30}")
                for entry in trend[-7:]:  # Chỉ hiển thị 7 mục gần nhất
                    date = entry.get("date", "N/A")
                    score = entry.get("avg_score", 0)
                    count = entry.get("sample_count", 0)
                    print(f"    {date:<12} {score:<10.2f} {count:<8}")
    
    # Hiển thị phản hồi gần đây
    print("\nPHẢN HỒI GẦN ĐÂY:")
    recent_feedback = report.get("recent_feedback", [])
    if recent_feedback:
        for idx, feedback in enumerate(recent_feedback[:5]):  # Chỉ hiển thị 5 phản hồi gần nhất
            query = feedback.get('query', '')
            if len(query) > 50:
                query = query[:47] + "..."
                
            print(f"\n  [{idx+1}] Query: {query}")
            print(f"      Mô hình: {feedback.get('model', '')}")
            print(f"      Điểm: {feedback.get('score', 'N/A')}")
            if feedback.get('feedback_text'):
                feedback_text = feedback.get('feedback_text', '')
                if len(feedback_text) > 70:
                    feedback_text = feedback_text[:67] + "..."
                print(f"      Nhận xét: {feedback_text}")
            
            timestamp = feedback.get('timestamp', '')
            if timestamp and len(timestamp) > 19:
                timestamp = timestamp[:19]
            print(f"      Thời gian: {timestamp}")
    else:
        print("  Chưa có phản hồi nào được ghi lại.")
    
    # Hiển thị trạng thái tối ưu hóa
    print("\nTRẠNG THÁI TỐI ƯU HÓA:")
    print(f"  Tối ưu hóa: {'BẬT' if report.get('optimization_enabled', False) else 'TẮT'}")
    print(f"  Thu thập phản hồi: {'BẬT' if report.get('feedback_enabled', False) else 'TẮT'}")
    
    # Thời gian tạo báo cáo
    generated_at = report.get("generated_at", "N/A")
    if isinstance(generated_at, str) and len(generated_at) > 19:
        generated_at = generated_at[:19]
    print(f"\nBáo cáo được tạo vào: {generated_at}")
    print("="*70)

def generate_optimization_summary(stats: Dict[str, Any]) -> str:
    """
    Tạo bản tóm tắt về quá trình tối ưu hóa.
    
    Args:
        stats: Thống kê tối ưu hóa
        
    Returns:
        Chuỗi tóm tắt
    """
    lines = []
    lines.append("TÓM TẮT TỐI ƯU HÓA:")
    
    # Thông tin cơ bản
    total_feedback = stats.get("total_feedback_count", 0)
    model_count = stats.get("model_count", 0)
    lines.append(f"- Tổng số phản hồi đã thu thập: {total_feedback}")
    lines.append(f"- Số lượng mô hình được đánh giá: {model_count}")
    
    # Phân tích trọng số
    if "current_weights" in stats:
        weights = stats["current_weights"]
        if weights:
            max_model = max(weights.items(), key=lambda x: x[1])[0]
            min_model = min(weights.items(), key=lambda x: x[1])[0]
            lines.append(f"- Mô hình được ưa thích nhất: {max_model} (trọng số: {weights[max_model]:.2f})")
            lines.append(f"- Mô hình ít được ưa thích nhất: {min_model} (trọng số: {weights[min_model]:.2f})")
    
    # Thống kê phản hồi
    if "feedback_counts_by_model" in stats:
        feedback_counts = stats["feedback_counts_by_model"]
        if feedback_counts:
            most_feedback_model = max(feedback_counts.items(), key=lambda x: x[1])[0]
            lines.append(f"- Mô hình có nhiều phản hồi nhất: {most_feedback_model} ({feedback_counts[most_feedback_model]} phản hồi)")
    
    # Thêm timestamp
    timestamp = stats.get("timestamp", "")
    if timestamp and len(timestamp) > 19:
        timestamp = timestamp[:19]
    lines.append(f"- Cập nhật lần cuối: {timestamp}")
    
    return "\n".join(lines)

def export_report_to_file(report: Dict[str, Any], output_path: str) -> bool:
    """
    Xuất báo cáo hiệu suất ra file.
    
    Args:
        report: Dữ liệu báo cáo
        output_path: Đường dẫn file đầu ra
        
    Returns:
        True nếu xuất thành công, False nếu có lỗi
    """
    try:
        import json
        
        # Thêm metadata
        report["export_metadata"] = {
            "exported_at": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Đã xuất báo cáo hiệu suất ra {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi xuất báo cáo hiệu suất: {e}")
        return False