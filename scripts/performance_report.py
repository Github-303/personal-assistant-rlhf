#!/usr/bin/env python
"""
Script tạo báo cáo hiệu suất của hệ thống trợ lý và các mô hình
"""

import os
import sys
import argparse
import logging
import json
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

# Thêm thư mục gốc vào đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimization.feedback_store import FeedbackStore
from src.cli.setup import setup_logging

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Tạo báo cáo hiệu suất của hệ thống")
    parser.add_argument("--db", type=str, default="data/feedback.db",
                        help="Đường dẫn đến file cơ sở dữ liệu phản hồi")
    parser.add_argument("--output-dir", type=str, default="reports",
                        help="Thư mục lưu báo cáo")
    parser.add_argument("--format", type=str, choices=["html", "md", "json", "csv", "all"], 
                        default="all", help="Định dạng báo cáo")
    parser.add_argument("--period", type=str, choices=["day", "week", "month", "all"], 
                        default="all", help="Khoảng thời gian phân tích")
    parser.add_argument("--visualize", action="store_true", 
                        help="Tạo biểu đồ trực quan")
    parser.add_argument("--model", type=str, help="Chỉ báo cáo cho mô hình cụ thể")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Mức độ ghi log")
    
    return parser.parse_args()

def filter_by_period(data: List[Dict], period: str) -> List[Dict]:
    """
    Lọc dữ liệu theo khoảng thời gian
    
    Args:
        data: Danh sách dữ liệu
        period: Khoảng thời gian (day, week, month, all)
        
    Returns:
        Danh sách dữ liệu đã lọc
    """
    if period == "all":
        return data
        
    now = datetime.now()
    
    if period == "day":
        start_time = now - timedelta(days=1)
    elif period == "week":
        start_time = now - timedelta(days=7)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        return data
        
    # Chuyển đổi sang datetime và lọc
    filtered_data = []
    for item in data:
        timestamp_str = item.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp >= start_time:
                filtered_data.append(item)
        except (ValueError, TypeError):
            # Bỏ qua nếu định dạng timestamp không hợp lệ
            continue
            
    return filtered_data

def filter_by_model(data: List[Dict], model_name: str) -> List[Dict]:
    """
    Lọc dữ liệu theo tên mô hình
    
    Args:
        data: Danh sách dữ liệu
        model_name: Tên mô hình
        
    Returns:
        Danh sách dữ liệu đã lọc
    """
    if not model_name:
        return data
        
    filtered_data = []
    for item in data:
        if item.get("type") == "pairwise_comparison":
            if (item.get("chosen_model") == model_name or 
                item.get("rejected_model") == model_name):
                filtered_data.append(item)
        else:
            if item.get("selected_response") == model_name:
                filtered_data.append(item)
                
    return filtered_data

def generate_stats(feedback_data: List[Dict]) -> Dict[str, Any]:
    """
    Tạo thống kê từ dữ liệu phản hồi
    
    Args:
        feedback_data: Danh sách phản hồi
        
    Returns:
        Dict chứa các thống kê
    """
    # Phân loại dữ liệu
    feedback_items = [item for item in feedback_data if item.get("type") != "pairwise_comparison"]
    comparison_items = [item for item in feedback_data if item.get("type") == "pairwise_comparison"]
    
    # Thống kê chung
    total_feedback = len(feedback_items)
    total_comparisons = len(comparison_items)
    
    # Thống kê điểm phản hồi
    scores = [item.get("feedback_score") for item in feedback_items if item.get("feedback_score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    score_distribution = {
        "excellent": sum(1 for s in scores if s >= 0.8),
        "good": sum(1 for s in scores if 0.6 <= s < 0.8),
        "average": sum(1 for s in scores if 0.4 <= s < 0.6),
        "poor": sum(1 for s in scores if 0.2 <= s < 0.4),
        "bad": sum(1 for s in scores if s < 0.2)
    }
    
    # Thống kê theo mô hình
    model_stats = {}
    for item in feedback_items:
        model = item.get("selected_response", "unknown")
        if model not in model_stats:
            model_stats[model] = {
                "count": 0,
                "scores": [],
                "wins": 0,
                "losses": 0
            }
        
        model_stats[model]["count"] += 1
        if item.get("feedback_score") is not None:
            model_stats[model]["scores"].append(item.get("feedback_score"))
    
    # Thêm thông tin từ so sánh cặp
    for item in comparison_items:
        chosen = item.get("chosen_model", "unknown")
        rejected = item.get("rejected_model", "unknown")
        
        if chosen not in model_stats:
            model_stats[chosen] = {"count": 0, "scores": [], "wins": 0, "losses": 0}
        if rejected not in model_stats:
            model_stats[rejected] = {"count": 0, "scores": [], "wins": 0, "losses": 0}
            
        model_stats[chosen]["wins"] += 1
        model_stats[rejected]["losses"] += 1
    
    # Tính toán thêm các thống kê cho mỗi mô hình
    for model, stats in model_stats.items():
        stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
        stats["win_rate"] = (stats["wins"] / (stats["wins"] + stats["losses"])) if (stats["wins"] + stats["losses"]) > 0 else 0
        
    # Thống kê theo thời gian
    timestamps = [datetime.fromisoformat(item.get("timestamp", datetime.now().isoformat())) 
                 for item in feedback_data if item.get("timestamp")]
    earliest = min(timestamps) if timestamps else datetime.now()
    latest = max(timestamps) if timestamps else datetime.now()
    timespan = (latest - earliest).days + 1
    
    # Thống kê theo ngày
    daily_stats = {}
    for item in feedback_data:
        try:
            date_str = datetime.fromisoformat(item.get("timestamp", "")).strftime("%Y-%m-%d")
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "feedback_count": 0,
                    "comparison_count": 0,
                    "scores": []
                }
                
            if item.get("type") == "pairwise_comparison":
                daily_stats[date_str]["comparison_count"] += 1
            else:
                daily_stats[date_str]["feedback_count"] += 1
                if item.get("feedback_score") is not None:
                    daily_stats[date_str]["scores"].append(item.get("feedback_score"))
                    
        except (ValueError, TypeError, AttributeError):
            continue
    
    # Tính điểm trung bình theo ngày
    for date, stats in daily_stats.items():
        stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else None
    
    return {
        "general": {
            "total_feedback": total_feedback,
            "total_comparisons": total_comparisons,
            "avg_score": avg_score,
            "score_distribution": score_distribution,
            "earliest_date": earliest.isoformat(),
            "latest_date": latest.isoformat(),
            "timespan_days": timespan
        },
        "models": model_stats,
        "daily": daily_stats
    }

def create_visualizations(stats: Dict[str, Any], output_dir: str) -> List[str]:
    """
    Tạo biểu đồ trực quan từ thống kê
    
    Args:
        stats: Dict chứa thống kê
        output_dir: Thư mục lưu biểu đồ
        
    Returns:
        Danh sách đường dẫn đến các biểu đồ
    """
    os.makedirs(output_dir, exist_ok=True)
    chart_files = []
    
    # 1. Biểu đồ phân phối điểm
    fig, ax = plt.subplots(figsize=(10, 6))
    categories = ["excellent", "good", "average", "poor", "bad"]
    values = [stats["general"]["score_distribution"][cat] for cat in categories]
    ax.bar(categories, values, color=['green', 'lightgreen', 'yellow', 'orange', 'red'])
    ax.set_title('Phân phối điểm phản hồi')
    ax.set_xlabel('Mức độ')
    ax.set_ylabel('Số lượng phản hồi')
    
    for i, v in enumerate(values):
        ax.text(i, v + 0.5, str(v), ha='center')
        
    score_dist_file = os.path.join(output_dir, 'score_distribution.png')
    fig.savefig(score_dist_file)
    plt.close(fig)
    chart_files.append(score_dist_file)
    
    # 2. Biểu đồ so sánh mô hình
    models = list(stats["models"].keys())
    if len(models) > 1:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Biểu đồ số lượng theo ngày
        ax1.plot(dates, feedback_counts, marker='o', color='blue', label='Phản hồi')
        ax1.plot(dates, comparison_counts, marker='x', color='orange', label='So sánh')
        ax1.set_title('Số lượng phản hồi theo ngày')
        ax1.set_ylabel('Số lượng')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Biểu đồ điểm trung bình theo ngày
        ax2.plot(dates, avg_scores, marker='s', color='green')
        ax2.set_title('Điểm trung bình theo ngày')
        ax2.set_xlabel('Ngày')
        ax2.set_ylabel('Điểm trung bình')
        ax2.set_ylim(0, 1)
        ax2.grid(True, alpha=0.3)
        
        # Xoay các nhãn ngày
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        fig.tight_layout()
        time_trend_file = os.path.join(output_dir, 'time_trends.png')
        fig.savefig(time_trend_file)
        plt.close(fig)
        chart_files.append(time_trend_file)
    
    return chart_files

def generate_html_report(stats: Dict[str, Any], chart_files: List[str], output_file: str) -> None:
    """
    Tạo báo cáo HTML
    
    Args:
        stats: Dict chứa thống kê
        chart_files: Danh sách đường dẫn đến các biểu đồ
        output_file: Đường dẫn file xuất
    """
    # Chuẩn bị dữ liệu biểu đồ
    charts_html = ""
    for chart_file in chart_files:
        rel_path = os.path.basename(chart_file)
        charts_html += f'<div class="chart-container"><img src="{rel_path}" alt="Chart" class="chart"></div>\n'
    
    # Chuẩn bị dữ liệu mô hình
    models_html = ""
    for model, model_stats in stats["models"].items():
        avg_score = model_stats["avg_score"]
        win_rate = model_stats["win_rate"]
        count = model_stats["count"]
        wins = model_stats["wins"]
        losses = model_stats["losses"]
        
        models_html += f"""
        <div class="model-card">
            <h3>{model}</h3>
            <div class="model-stats">
                <p><strong>Số lần sử dụng:</strong> {count}</p>
                <p><strong>Điểm trung bình:</strong> {avg_score:.2f}</p>
                <p><strong>Tỷ lệ thắng:</strong> {win_rate:.2f} ({wins} thắng / {losses} thua)</p>
            </div>
        </div>
        """
    
    # Tạo bảng thống kê theo ngày
    daily_html = """
    <div class="daily-stats">
        <h2>Thống kê theo ngày</h2>
        <table>
            <thead>
                <tr>
                    <th>Ngày</th>
                    <th>Phản hồi</th>
                    <th>So sánh</th>
                    <th>Điểm TB</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for date in sorted(stats["daily"].keys(), reverse=True):
        day_stats = stats["daily"][date]
        feedback_count = day_stats["feedback_count"]
        comparison_count = day_stats["comparison_count"]
        avg_score = day_stats["avg_score"]
        avg_score_str = f"{avg_score:.2f}" if avg_score is not None else "N/A"
        
        daily_html += f"""
                <tr>
                    <td>{date}</td>
                    <td>{feedback_count}</td>
                    <td>{comparison_count}</td>
                    <td>{avg_score_str}</td>
                </tr>
        """
    
    daily_html += """
            </tbody>
        </table>
    </div>
    """
    
    # Tạo HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Báo cáo hiệu suất hệ thống trợ lý</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            header {{
                background-color: #0066cc;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .summary-box {{
                background-color: white;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 20px;
            }}
            .summary-item {{
                text-align: center;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            .summary-value {{
                font-size: 24px;
                font-weight: bold;
                color: #0066cc;
            }}
            .summary-label {{
                font-size: 14px;
                color: #666;
            }}
            .chart-container {{
                background-color: white;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .chart {{
                max-width: 100%;
                height: auto;
            }}
            .model-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            .model-card {{
                background-color: white;
                border-radius: 5px;
                padding: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            h2, h3 {{
                color: #0066cc;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            footer {{
                text-align: center;
                margin-top: 40px;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Báo cáo hiệu suất hệ thống trợ lý</h1>
            <p>Tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="summary-box">
            <h2>Tổng quan</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["total_feedback"]}</div>
                    <div class="summary-label">Phản hồi</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["total_comparisons"]}</div>
                    <div class="summary-label">So sánh</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["avg_score"]:.2f}</div>
                    <div class="summary-label">Điểm trung bình</div>
                </div>
            </div>
            
            <h3>Phân phối điểm</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["score_distribution"]["excellent"]}</div>
                    <div class="summary-label">Xuất sắc (≥0.8)</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["score_distribution"]["good"]}</div>
                    <div class="summary-label">Tốt (0.6-0.8)</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["score_distribution"]["average"]}</div>
                    <div class="summary-label">Trung bình (0.4-0.6)</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["score_distribution"]["poor"]}</div>
                    <div class="summary-label">Kém (0.2-0.4)</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["score_distribution"]["bad"]}</div>
                    <div class="summary-label">Tệ (<0.2)</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{stats["general"]["timespan_days"]}</div>
                    <div class="summary-label">Số ngày thu thập</div>
                </div>
            </div>
        </div>
        
        {charts_html}
        
        <div class="summary-box">
            <h2>Hiệu suất theo mô hình</h2>
            <div class="model-grid">
                {models_html}
            </div>
        </div>
        
        {daily_html}
        
        <footer>
            <p>Báo cáo được tạo tự động bởi hệ thống trợ lý cá nhân với RLHF và DPO</p>
            <p>Khoảng thời gian: {stats["general"]["earliest_date"]} đến {stats["general"]["latest_date"]}</p>
        </footer>
    </body>
    </html>
    """
    
    # Ghi ra file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Sao chép các file biểu đồ vào thư mục output
    output_dir = os.path.dirname(output_file)
    for chart_file in chart_files:
        if os.path.dirname(chart_file) != output_dir:
            import shutil
            shutil.copy2(chart_file, output_dir)

def generate_markdown_report(stats: Dict[str, Any], chart_files: List[str], output_file: str) -> None:
    """
    Tạo báo cáo Markdown
    
    Args:
        stats: Dict chứa thống kê
        chart_files: Danh sách đường dẫn đến các biểu đồ
        output_file: Đường dẫn file xuất
    """
    # Chuẩn bị dữ liệu biểu đồ
    charts_md = ""
    for chart_file in chart_files:
        rel_path = os.path.basename(chart_file)
        charts_md += f"![Chart]({rel_path})\n\n"
    
    # Tạo Markdown
    markdown = f"""
# Báo cáo hiệu suất hệ thống trợ lý
*Tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Tổng quan

- **Tổng số phản hồi:** {stats["general"]["total_feedback"]}
- **Tổng số so sánh:** {stats["general"]["total_comparisons"]}
- **Điểm trung bình:** {stats["general"]["avg_score"]:.2f}
- **Khoảng thời gian:** {stats["general"]["timespan_days"]} ngày ({stats["general"]["earliest_date"]} đến {stats["general"]["latest_date"]})

### Phân phối điểm

- **Xuất sắc (≥0.8):** {stats["general"]["score_distribution"]["excellent"]}
- **Tốt (0.6-0.8):** {stats["general"]["score_distribution"]["good"]}
- **Trung bình (0.4-0.6):** {stats["general"]["score_distribution"]["average"]}
- **Kém (0.2-0.4):** {stats["general"]["score_distribution"]["poor"]}
- **Tệ (<0.2):** {stats["general"]["score_distribution"]["bad"]}

## Biểu đồ

{charts_md}

## Hiệu suất theo mô hình

"""
    
    # Thêm thông tin mô hình
    for model, model_stats in stats["models"].items():
        avg_score = model_stats["avg_score"]
        win_rate = model_stats["win_rate"]
        count = model_stats["count"]
        wins = model_stats["wins"]
        losses = model_stats["losses"]
        
        markdown += f"""
### {model}
- **Số lần sử dụng:** {count}
- **Điểm trung bình:** {avg_score:.2f}
- **Tỷ lệ thắng:** {win_rate:.2f} ({wins} thắng / {losses} thua)

"""
    
    # Thêm thống kê theo ngày
    markdown += "## Thống kê theo ngày\n\n"
    markdown += "| Ngày | Phản hồi | So sánh | Điểm TB |\n"
    markdown += "|------|----------|---------|--------|\n"
    
    for date in sorted(stats["daily"].keys(), reverse=True):
        day_stats = stats["daily"][date]
        feedback_count = day_stats["feedback_count"]
        comparison_count = day_stats["comparison_count"]
        avg_score = day_stats["avg_score"]
        avg_score_str = f"{avg_score:.2f}" if avg_score is not None else "N/A"
        
        markdown += f"| {date} | {feedback_count} | {comparison_count} | {avg_score_str} |\n"
    
    markdown += "\n\n---\n\n*Báo cáo được tạo tự động bởi hệ thống trợ lý cá nhân với RLHF và DPO*"
    
    # Ghi ra file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    # Sao chép các file biểu đồ vào thư mục output
    output_dir = os.path.dirname(output_file)
    for chart_file in chart_files:
        if os.path.dirname(chart_file) != output_dir:
            import shutil
            shutil.copy2(chart_file, output_dir)

def export_to_csv(stats: Dict[str, Any], output_dir: str) -> List[str]:
    """
    Xuất thống kê sang CSV
    
    Args:
        stats: Dict chứa thống kê
        output_dir: Thư mục xuất
        
    Returns:
        Danh sách đường dẫn đến các file CSV
    """
    import csv
    os.makedirs(output_dir, exist_ok=True)
    files_created = []
    
    # 1. Thống kê tổng quan
    summary_file = os.path.join(output_dir, 'summary.csv')
    with open(summary_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Feedback', stats["general"]["total_feedback"]])
        writer.writerow(['Total Comparisons', stats["general"]["total_comparisons"]])
        writer.writerow(['Average Score', stats["general"]["avg_score"]])
        writer.writerow(['Timespan (days)', stats["general"]["timespan_days"]])
        writer.writerow(['Earliest Date', stats["general"]["earliest_date"]])
        writer.writerow(['Latest Date', stats["general"]["latest_date"]])
        
        writer.writerow(['', ''])
        writer.writerow(['Score Distribution', ''])
        for category, count in stats["general"]["score_distribution"].items():
            writer.writerow([f'{category.capitalize()}', count])
    
    files_created.append(summary_file)
    
    # 2. Thống kê mô hình
    models_file = os.path.join(output_dir, 'models.csv')
    with open(models_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Model', 'Usage Count', 'Average Score', 'Win Rate', 'Wins', 'Losses'])
        
        for model, model_stats in stats["models"].items():
            writer.writerow([
                model,
                model_stats["count"],
                model_stats["avg_score"],
                model_stats["win_rate"],
                model_stats["wins"],
                model_stats["losses"]
            ])
    
    files_created.append(models_file)
    
    # 3. Thống kê theo ngày
    daily_file = os.path.join(output_dir, 'daily_stats.csv')
    with open(daily_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Feedback Count', 'Comparison Count', 'Average Score'])
        
        for date in sorted(stats["daily"].keys()):
            day_stats = stats["daily"][date]
            avg_score = day_stats["avg_score"] if day_stats["avg_score"] is not None else ''
            
            writer.writerow([
                date,
                day_stats["feedback_count"],
                day_stats["comparison_count"],
                avg_score
            ])
    
    files_created.append(daily_file)
    
    return files_created

def export_to_json(stats: Dict[str, Any], output_file: str) -> None:
    """
    Xuất thống kê sang JSON
    
    Args:
        stats: Dict chứa thống kê
        output_file: Đường dẫn file xuất
    """
    # Thêm metadata
    export_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        },
        "statistics": stats
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

def main():
    """Main function"""
    args = parse_args()
    
    # Thiết lập logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    logger = logging.getLogger("performance_report")
    
    # Tạo thư mục output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, f"performance_report_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Sẽ lưu báo cáo vào: {output_dir}")
    
    # Khởi tạo FeedbackStore
    store = FeedbackStore(args.db)
    
    # Lấy tất cả phản hồi
    logger.info("Đang lấy dữ liệu phản hồi...")
    feedback_data = store.get_all_feedback()
    logger.info(f"Đã lấy {len(feedback_data)} bản ghi phản hồi")
    
    # Lọc dữ liệu
    feedback_data = filter_by_period(feedback_data, args.period)
    if args.model:
        feedback_data = filter_by_model(feedback_data, args.model)
    logger.info(f"Còn lại {len(feedback_data)} bản ghi sau khi lọc")
    
    if not feedback_data:
        logger.warning("Không có dữ liệu để tạo báo cáo")
        return
    
    # Tạo thống kê
    logger.info("Đang tạo thống kê...")
    stats = generate_stats(feedback_data)
    
    # Tạo biểu đồ nếu yêu cầu
    chart_files = []
    if args.visualize:
        logger.info("Đang tạo biểu đồ trực quan...")
        charts_dir = os.path.join(output_dir, 'charts')
        chart_files = create_visualizations(stats, charts_dir)
        logger.info(f"Đã tạo {len(chart_files)} biểu đồ")
    
    # Xuất báo cáo theo định dạng yêu cầu
    formats_to_export = [args.format] if args.format != "all" else ["html", "md", "json", "csv"]
    
    for format in formats_to_export:
        if format == "html":
            logger.info("Đang tạo báo cáo HTML...")
            html_file = os.path.join(output_dir, 'performance_report.html')
            generate_html_report(stats, chart_files, html_file)
            logger.info(f"Đã tạo báo cáo HTML: {html_file}")
            
        elif format == "md":
            logger.info("Đang tạo báo cáo Markdown...")
            md_file = os.path.join(output_dir, 'performance_report.md')
            generate_markdown_report(stats, chart_files, md_file)
            logger.info(f"Đã tạo báo cáo Markdown: {md_file}")
            
        elif format == "json":
            logger.info("Đang xuất dữ liệu JSON...")
            json_file = os.path.join(output_dir, 'performance_stats.json')
            export_to_json(stats, json_file)
            logger.info(f"Đã xuất dữ liệu JSON: {json_file}")
            
        elif format == "csv":
            logger.info("Đang xuất dữ liệu CSV...")
            csv_dir = os.path.join(output_dir, 'csv')
            csv_files = export_to_csv(stats, csv_dir)
            logger.info(f"Đã xuất {len(csv_files)} file CSV vào {csv_dir}")
    
    logger.info(f"Báo cáo hiệu suất đã được tạo thành công trong thư mục: {output_dir}")
def create_visualizations(stats: Dict[str, Any], output_dir: str) -> List[str]:
    """
    Tạo biểu đồ trực quan từ thống kê
    
    Args:
        stats: Dict chứa thống kê
        output_dir: Thư mục lưu biểu đồ
        
    Returns:
        Danh sách đường dẫn đến các biểu đồ
    """
    os.makedirs(output_dir, exist_ok=True)
    chart_files = []
    
    # 1. Biểu đồ phân phối điểm
    fig, ax = plt.subplots(figsize=(10, 6))
    categories = ["excellent", "good", "average", "poor", "bad"]
    values = [stats["general"]["score_distribution"][cat] for cat in categories]
    ax.bar(categories, values, color=['green', 'lightgreen', 'yellow', 'orange', 'red'])
    ax.set_title('Phân phối điểm phản hồi')
    ax.set_xlabel('Mức độ')
    ax.set_ylabel('Số lượng phản hồi')
    
    for i, v in enumerate(values):
        ax.text(i, v + 0.5, str(v), ha='center')
        
    score_dist_file = os.path.join(output_dir, 'score_distribution.png')
    fig.savefig(score_dist_file)
    plt.close(fig)
    chart_files.append(score_dist_file)
    
    # 2. Biểu đồ so sánh mô hình
    models = list(stats["models"].keys())
    if len(models) > 1:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
        
        # Biểu đồ điểm trung bình
        avg_scores = [stats["models"][m]["avg_score"] for m in models]
        ax1.bar(models, avg_scores, color='skyblue')
        ax1.set_title('Điểm trung bình theo mô hình')
        ax1.set_xlabel('Mô hình')
        ax1.set_ylabel('Điểm trung bình')
        ax1.set_ylim(0, 1)
        
        for i, v in enumerate(avg_scores):
            ax1.text(i, v + 0.05, f"{v:.2f}", ha='center')
            
        # Biểu đồ tỷ lệ thắng
        win_rates = [stats["models"][m]["win_rate"] for m in models]
        ax2.bar(models, win_rates, color='lightgreen')
        ax2.set_title('Tỷ lệ thắng theo mô hình')
        ax2.set_xlabel('Mô hình')
        ax2.set_ylabel('Tỷ lệ thắng')
        ax2.set_ylim(0, 1)
        
        for i, v in enumerate(win_rates):
            ax2.text(i, v + 0.05, f"{v:.2f}", ha='center')
            
        fig.tight_layout()
        model_comp_file = os.path.join(output_dir, 'model_comparison.png')
        fig.savefig(model_comp_file)
        plt.close(fig)
        chart_files.append(model_comp_file)
    
    # 3. Biểu đồ xu hướng theo thời gian
    daily_data = stats["daily"]
    if len(daily_data) > 1:
        # Chuyển đổi thành DataFrame
        dates = sorted(daily_data.keys())
        feedback_counts = [daily_data[d]["feedback_count"] for d in dates]
        comparison_counts = [daily_data[d]["comparison_count"] for d in dates]
        avg_scores = [daily_data[d]["avg_score"] if daily_data[d]["avg_score"] is not None else 0 for d in dates]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Biểu đồ số lượng theo ngày
        ax1.plot(dates, feedback_counts, marker='o', color='blue', label='Phản hồi')
        ax1.plot(dates, comparison_counts, marker='x', color='orange', label='So sánh')
        ax1.set_title('Số lượng phản hồi theo ngày')
        ax1.set_ylabel('Số lượng')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Biểu đồ điểm trung bình theo ngày
        ax2.plot(dates, avg_scores, marker='s', color='green')
        ax2.set_title('Điểm trung bình theo ngày')
        ax2.set_xlabel('Ngày')
        ax2.set_ylabel('Điểm trung bình')
        ax2.set_ylim(0, 1)
        ax2.grid(True, alpha=0.3)
        
        # Xoay các nhãn ngày
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        fig.tight_layout()
        time_trend_file = os.path.join(output_dir, 'time_trends.png')
        fig.savefig(time_trend_file)
        plt.close(fig)
        chart_files.append(time_trend_file)
    
    return chart_files
if __name__ == "__main__":
    main() 
    