#!/usr/bin/env python
"""
Script xuất dữ liệu phản hồi cho huấn luyện RLHF
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Thêm thư mục gốc vào đường dẫn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimization.feedback_store import FeedbackStore
from src.cli.setup import setup_logging

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Xuất dữ liệu phản hồi cho huấn luyện RLHF")
    parser.add_argument("--db", type=str, default="data/feedback.db",
                        help="Đường dẫn đến file cơ sở dữ liệu phản hồi")
    parser.add_argument("--output-dir", type=str, default="data/rlhf_exports",
                        help="Thư mục xuất dữ liệu")
    parser.add_argument("--format", type=str, choices=["jsonl", "json", "csv"], default="jsonl",
                        help="Định dạng xuất (default: jsonl)")
    parser.add_argument("--min-score", type=float, help="Chỉ xuất phản hồi với điểm cao hơn")
    parser.add_argument("--max-feedback", type=int, help="Giới hạn số lượng phản hồi")
    parser.add_argument("--split", action="store_true", help="Chia thành tập train/eval")
    parser.add_argument("--eval-ratio", type=float, default=0.1, 
                        help="Tỷ lệ tập eval khi chia (default: 0.1)")
    parser.add_argument("--backup", action="store_true", help="Sao lưu cơ sở dữ liệu trước khi xuất")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Mức độ ghi log")
    
    return parser.parse_args()

def export_feedback_to_jsonl(feedback_data: List[Dict], output_file: str) -> int:
    """
    Xuất dữ liệu phản hồi sang định dạng JSONL
    
    Args:
        feedback_data: Danh sách phản hồi
        output_file: Đường dẫn file xuất
        
    Returns:
        Số lượng bản ghi đã xuất
    """
    count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in feedback_data:
            # Chuyển đổi sang định dạng RLHF
            if item.get("type") == "pairwise_comparison":
                # Bản ghi so sánh
                rlhf_item = {
                    "prompt": item.get("query", ""),
                    "chosen": item.get("chosen", ""),
                    "rejected": item.get("rejected", ""),
                    "chosen_model": item.get("chosen_model", ""),
                    "rejected_model": item.get("rejected_model", ""),
                    "conversation_id": item.get("conversation_id", ""),
                    "timestamp": item.get("timestamp", "")
                }
            else:
                # Bản ghi phản hồi
                selected_response = item.get("selected_response", "")
                responses = item.get("responses", {})
                response_text = responses.get(selected_response, "")
                
                rlhf_item = {
                    "prompt": item.get("query", ""),
                    "response": response_text,
                    "score": item.get("feedback_score"),
                    "model": selected_response,
                    "feedback": item.get("feedback_text"),
                    "conversation_id": item.get("conversation_id", ""),
                    "timestamp": item.get("timestamp", "")
                }
                
            f.write(json.dumps(rlhf_item, ensure_ascii=False) + '\n')
            count += 1
            
    return count

def export_feedback_to_json(feedback_data: List[Dict], output_file: str, 
                           split: bool = False, eval_ratio: float = 0.1) -> Dict:
    """
    Xuất dữ liệu phản hồi sang định dạng JSON
    
    Args:
        feedback_data: Danh sách phản hồi
        output_file: Đường dẫn file xuất
        split: Chia thành tập train/eval
        eval_ratio: Tỷ lệ tập eval
        
    Returns:
        Dict thống kê số lượng bản ghi đã xuất
    """
    # Phân loại dữ liệu
    comparisons = []
    feedback = []
    
    for item in feedback_data:
        if item.get("type") == "pairwise_comparison":
            comparisons.append({
                "prompt": item.get("query", ""),
                "chosen": item.get("chosen", ""),
                "rejected": item.get("rejected", ""),
                "chosen_model": item.get("chosen_model", ""),
                "rejected_model": item.get("rejected_model", ""),
                "conversation_id": item.get("conversation_id", ""),
                "timestamp": item.get("timestamp", "")
            })
        else:
            selected_response = item.get("selected_response", "")
            responses = item.get("responses", {})
            response_text = responses.get(selected_response, "")
            
            feedback.append({
                "prompt": item.get("query", ""),
                "response": response_text,
                "score": item.get("feedback_score"),
                "model": selected_response,
                "feedback": item.get("feedback_text"),
                "conversation_id": item.get("conversation_id", ""),
                "timestamp": item.get("timestamp", "")
            })
    
    # Chia thành tập train/eval nếu cần
    if split and feedback:
        import random
        random.shuffle(feedback)
        split_idx = max(1, int(len(feedback) * (1 - eval_ratio)))
        train_feedback = feedback[:split_idx]
        eval_feedback = feedback[split_idx:]
    else:
        train_feedback = feedback
        eval_feedback = []
        
    if split and comparisons:
        import random
        random.shuffle(comparisons)
        split_idx = max(1, int(len(comparisons) * (1 - eval_ratio)))
        train_comparisons = comparisons[:split_idx]
        eval_comparisons = comparisons[split_idx:]
    else:
        train_comparisons = comparisons
        eval_comparisons = []
    
    # Tạo cấu trúc dữ liệu xuất
    export_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "split": split
        },
        "train": {
            "feedback": train_feedback,
            "comparisons": train_comparisons
        }
    }
    
    if split:
        export_data["eval"] = {
            "feedback": eval_feedback,
            "comparisons": eval_comparisons
        }
    
    # Ghi ra file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
        
    return {
        "total": len(feedback) + len(comparisons),
        "feedback": len(feedback),
        "comparisons": len(comparisons),
        "train_feedback": len(train_feedback),
        "train_comparisons": len(train_comparisons),
        "eval_feedback": len(eval_feedback) if split else 0,
        "eval_comparisons": len(eval_comparisons) if split else 0
    }

def export_feedback_to_csv(feedback_data: List[Dict], output_dir: str) -> Dict:
    """
    Xuất dữ liệu phản hồi sang định dạng CSV
    
    Args:
        feedback_data: Danh sách phản hồi
        output_dir: Thư mục xuất
        
    Returns:
        Dict thống kê số lượng bản ghi đã xuất
    """
    import csv
    
    # Phân loại dữ liệu
    comparisons = []
    feedback = []
    
    for item in feedback_data:
        if item.get("type") == "pairwise_comparison":
            comparisons.append({
                "prompt": item.get("query", ""),
                "chosen": item.get("chosen", ""),
                "rejected": item.get("rejected", ""),
                "chosen_model": item.get("chosen_model", ""),
                "rejected_model": item.get("rejected_model", ""),
                "conversation_id": item.get("conversation_id", ""),
                "timestamp": item.get("timestamp", "")
            })
        else:
            selected_response = item.get("selected_response", "")
            responses = item.get("responses", {})
            response_text = responses.get(selected_response, "")
            
            feedback.append({
                "prompt": item.get("query", ""),
                "response": response_text,
                "score": item.get("feedback_score"),
                "model": selected_response,
                "feedback": item.get("feedback_text"),
                "conversation_id": item.get("conversation_id", ""),
                "timestamp": item.get("timestamp", "")
            })
    
    # Xuất phản hồi
    feedback_file = os.path.join(output_dir, "feedback.csv")
    feedback_count = 0
    if feedback:
        with open(feedback_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ["prompt", "response", "score", "model", "feedback", 
                        "conversation_id", "timestamp"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in feedback:
                writer.writerow(item)
                feedback_count += 1
    
    # Xuất so sánh
    comparison_file = os.path.join(output_dir, "comparisons.csv")
    comparison_count = 0
    if comparisons:
        with open(comparison_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ["prompt", "chosen", "rejected", "chosen_model", 
                        "rejected_model", "conversation_id", "timestamp"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in comparisons:
                writer.writerow(item)
                comparison_count += 1
                
    return {
        "total": feedback_count + comparison_count,
        "feedback": feedback_count,
        "comparisons": comparison_count,
        "feedback_file": feedback_file if feedback_count > 0 else None,
        "comparison_file": comparison_file if comparison_count > 0 else None
    }

def filter_feedback_data(feedback_data: List[Dict], min_score: Optional[float] = None,
                        max_count: Optional[int] = None) -> List[Dict]:
    """
    Lọc dữ liệu phản hồi theo điểm và số lượng
    
    Args:
        feedback_data: Danh sách phản hồi
        min_score: Điểm tối thiểu
        max_count: Số lượng tối đa
        
    Returns:
        Danh sách phản hồi đã lọc
    """
    # Lọc theo điểm
    if min_score is not None:
        feedback_data = [
            item for item in feedback_data
            if (item.get("type") == "pairwise_comparison") or 
               (item.get("feedback_score") is not None and 
                item.get("feedback_score") >= min_score)
        ]
    
    # Giới hạn số lượng
    if max_count is not None and max_count > 0:
        feedback_data = feedback_data[:max_count]
        
    return feedback_data

def main():
    """Main function"""
    args = parse_args()
    
    # Thiết lập logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    logger = logging.getLogger("export_rlhf")
    
    # Tạo thư mục xuất
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Khởi tạo FeedbackStore
    store = FeedbackStore(args.db)
    
    # Sao lưu cơ sở dữ liệu nếu cần
    if args.backup:
        logger.info("Đang sao lưu cơ sở dữ liệu...")
        backup_success = store.backup_database()
        if backup_success:
            logger.info("Đã sao lưu cơ sở dữ liệu thành công")
        else:
            logger.warning("Không thể sao lưu cơ sở dữ liệu")
    
    # Lấy tất cả phản hồi
    logger.info("Đang lấy dữ liệu phản hồi...")
    feedback_data = store.get_all_feedback()
    logger.info(f"Đã lấy {len(feedback_data)} bản ghi phản hồi")
    
    # Lọc dữ liệu
    feedback_data = filter_feedback_data(
        feedback_data, 
        min_score=args.min_score,
        max_count=args.max_feedback
    )
    logger.info(f"Còn lại {len(feedback_data)} bản ghi sau khi lọc")
    
    if not feedback_data:
        logger.warning("Không có dữ liệu để xuất")
        return
    
    # Tạo tên file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Xuất dữ liệu theo định dạng
    if args.format == "jsonl":
        output_file = os.path.join(args.output_dir, f"rlhf_export_{timestamp}.jsonl")
        count = export_feedback_to_jsonl(feedback_data, output_file)
        logger.info(f"Đã xuất {count} bản ghi sang {output_file}")
        
    elif args.format == "json":
        output_file = os.path.join(args.output_dir, f"rlhf_export_{timestamp}.json")
        stats = export_feedback_to_json(
            feedback_data, output_file, 
            split=args.split, eval_ratio=args.eval_ratio
        )
        logger.info(f"Đã xuất {stats['total']} bản ghi sang {output_file}")
        if args.split:
            logger.info(f"  - Train: {stats['train_feedback']} phản hồi, {stats['train_comparisons']} so sánh")
            logger.info(f"  - Eval: {stats['eval_feedback']} phản hồi, {stats['eval_comparisons']} so sánh")
            
    elif args.format == "csv":
        output_subdir = os.path.join(args.output_dir, f"rlhf_export_{timestamp}")
        os.makedirs(output_subdir, exist_ok=True)
        stats = export_feedback_to_csv(feedback_data, output_subdir)
        logger.info(f"Đã xuất {stats['total']} bản ghi sang {output_subdir}")
        logger.info(f"  - {stats['feedback']} phản hồi: {os.path.basename(stats['feedback_file']) if stats['feedback_file'] else 'None'}")
        logger.info(f"  - {stats['comparisons']} so sánh: {os.path.basename(stats['comparison_file']) if stats['comparison_file'] else 'None'}")

if __name__ == "__main__":
    main()