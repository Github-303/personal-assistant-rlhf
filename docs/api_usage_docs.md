# API Reference

Tài liệu này mô tả các API chính của hệ thống hỗ trợ cá nhân nâng cao với RLHF và DPO. Các API này có thể được sử dụng để tích hợp hệ thống vào các ứng dụng khác hoặc mở rộng chức năng.

## Core API

### ModelManager

```python
from src.core.models import ModelManager

# Khởi tạo
model_manager = ModelManager(config)

# Phương thức chính
model = model_manager.get_model(role)  # Lấy đối tượng mô hình theo vai trò
config = model_manager.get_model_config(role)  # Lấy cấu hình mô hình
roles = model_manager.get_all_roles()  # Lấy danh sách vai trò
result = model_manager.generate_response(role, prompt, system_prompt, temperature, max_tokens)
```

### PersonalAssistant

```python
from src.core.assistant import PersonalAssistant

# Khởi tạo
assistant = PersonalAssistant(model_manager, config)

# Phương thức chính
result = assistant.process_query(query, role, temperature, max_tokens, system_prompt)
file_path = assistant.save_conversation(filename)  # Lưu hội thoại
success = assistant.load_conversation(file_path)  # Tải hội thoại
assistant.clear_conversation_history()  # Xóa lịch sử
summary = assistant.get_conversation_summary()  # Lấy tóm tắt hội thoại
```

### GroupDiscussionManager

```python
from src.core.group_discussion import GroupDiscussionManager

# Khởi tạo
group_manager = GroupDiscussionManager(model_manager, config)

# Phương thức chính
result = group_manager.conduct_discussion(
    query, 
    temperature, 
    max_tokens, 
    rounds, 
    participating_roles, 
    custom_system_prompts
)
```

## Optimization API

### FeedbackStore

```python
from src.optimization.feedback_store import FeedbackStore

# Khởi tạo
feedback_store = FeedbackStore(config)

# Phương thức chính
feedback_id = feedback_store.add_feedback(
    query, response, model, score, feedback_text, is_group_discussion, metadata
)
pair_id = feedback_store.add_preference_pair(
    query, chosen_response, rejected_response, chosen_model, rejected_model, metadata
)
metrics = feedback_store.get_model_metrics()
recent = feedback_store.get_recent_feedback(limit=10)
stats = feedback_store.get_preference_stats()
trend = feedback_store.get_model_performance_trend(model, time_window=30)
rlhf_data = feedback_store.export_rlhf_data()
```

### PreferenceOptimizer

```python
from src.optimization.preference_optimizer import PreferenceOptimizer

# Khởi tạo
preference_optimizer = PreferenceOptimizer(feedback_store, config)

# Phương thức chính
preference_optimizer.update_from_metrics()  # Cập nhật từ dữ liệu metrics
best_model, score = preference_optimizer.get_best_model_for_query(query)
query_type = preference_optimizer.analyze_query_type(query)
top_models = preference_optimizer.get_best_models_for_query(query, top_n=3)
should_use_group = preference_optimizer.should_use_group_discussion(query, models)
preference_optimizer.reset_weights(models=None)  # Đặt lại trọng số
performance = preference_optimizer.get_historical_performance(model)
```

### FeedbackCollector

```python
from src.optimization.feedback_collector import RLHFFeedbackCollector

# Khởi tạo
feedback_collector = RLHFFeedbackCollector(feedback_store, config)

# Phương thức chính
score = feedback_collector.collect_scalar_feedback(
    query, response, model, is_group_discussion, metadata
)
choice = feedback_collector.collect_comparative_feedback(query, responses, metadata)
should_collect = feedback_collector.check_should_collect_feedback(model, is_complex_query)
dataset_path = feedback_collector.export_rlhf_dataset()
```

### ResponseOptimizer

```python
from src.optimization.response_optimizer import ResponseOptimizer

# Khởi tạo
response_optimizer = ResponseOptimizer(feedback_store, preference_optimizer, config)

# Phương thức chính
optimized_prompt = response_optimizer.optimize_prompt(query, target_model)
optimized_system_prompt = response_optimizer.optimize_system_prompt(
    query, target_model, base_system_prompt
)
top_models = response_optimizer.get_best_models_for_query(query, top_n=2)
should_use_group = response_optimizer.should_use_group_discussion(query)
optimization_result = response_optimizer.optimize_query_result(query, selected_model)
```

### FeedbackOptimizationManager

```python
from src.optimization.manager import FeedbackOptimizationManager

# Khởi tạo
feedback_manager = FeedbackOptimizationManager(config)

# Phương thức chính
optimization = feedback_manager.optimize_query(query, selected_model)
system_prompt = feedback_manager.optimize_system_prompt(query, target_model, base_system_prompt)
score = feedback_manager.collect_feedback(query, response, model, is_group_discussion, metadata)
choice = feedback_manager.collect_comparative_feedback(query, responses, metadata)
feedback_manager.update_model_weights()
dataset_path = feedback_manager.export_rlhf_dataset()
report = feedback_manager.get_model_performance_report()
feedback_manager.toggle_optimization(enabled=True)
feedback_manager.toggle_feedback_collection(enabled=True)
stats = feedback_manager.get_optimization_stats()
feedback_manager.reset_optimization(reset_feedback_db=False)
```

## Integration API

### EnhancedPersonalAssistant

```python
from src.integration.enhanced_assistant import EnhancedPersonalAssistant

# Khởi tạo (thường qua AssistantFactory)
enhanced_assistant = EnhancedPersonalAssistant(
    base_assistant, group_discussion_manager, feedback_manager, config
)

# Phương thức chính
result = enhanced_assistant.process_query(
    query, role, temperature, max_tokens, group_discussion, rounds, collect_feedback, system_prompt
)
enhanced_assistant.toggle_optimization(enabled=True)
enhanced_assistant.toggle_feedback_collection(enabled=True)
enhanced_assistant.toggle_auto_select_model(enabled=True)
report = enhanced_assistant.get_performance_report()
dataset_path = enhanced_assistant.export_rlhf_dataset()
status = enhanced_assistant.get_optimization_status()
file_path = enhanced_assistant.save_conversation(filename)
```

### AssistantFactory

```python
from src.integration.interfaces import AssistantFactory, setup_assistant

# Phương thức tĩnh
config = AssistantFactory.load_config(config_path)
model_manager = AssistantFactory.create_model_manager(config)
base_assistant = AssistantFactory.create_base_assistant(config, model_manager)
group_manager = AssistantFactory.create_group_discussion_manager(config, model_manager)
feedback_manager = AssistantFactory.create_feedback_optimization_manager(config)
enhanced_assistant = AssistantFactory.create_enhanced_assistant(config)

# Hoặc sử dụng hàm tiện ích
assistant = setup_assistant(config_path)
```

## Utilities API

### PromptLibrary

```python
from src.utils.prompt_templates import PromptLibrary, load_prompt_library

# Khởi tạo
prompt_library = load_prompt_library(config)

# Phương thức chính
template = prompt_library.get_template(role, template_name)
formatted_prompt = prompt_library.format_prompt(role, template_name, query="Hello")
system_prompt = prompt_library.get_system_prompt(role)
```

### Export Utilities

```python
from src.utils.export import export_rlhf_data, export_performance_report, export_conversation_history, create_backup

# Các hàm tiện ích
output_file = export_rlhf_data(rlhf_data, export_dir)
files = export_performance_report(report, export_dir)
files = export_conversation_history(conversation_data, export_dir, formats=["json", "txt", "html", "csv"])
backup_path = create_backup(source_path, backup_dir)
```

## CLI API

```python
from src.cli.argparser import parse_args, update_config_from_args
from src.cli.interactive import run_interactive_mode, InteractiveShell
from src.cli.reporting import display_performance_report, export_report_to_file, generate_optimization_summary

# Phân tích tham số
args = parse_args()
updated_config = update_config_from_args(config, args)

# Chế độ tương tác
run_interactive_mode(assistant, args)

# Báo cáo
display_performance_report(report)
success = export_report_to_file(report, output_path)
summary = generate_optimization_summary(stats)
```

## Ví dụ sử dụng API

### Tạo trợ lý nâng cao và xử lý truy vấn

```python
from src.integration.interfaces import setup_assistant

# Tạo trợ lý nâng cao
assistant = setup_assistant("config/default.yml")

# Xử lý truy vấn với tối ưu hóa tự động
result = assistant.process_query(
    query="Viết một hàm Python để tìm số Fibonacci",
    temperature=0.7,
    group_discussion=True,
    collect_feedback=True
)

# Hiển thị kết quả
if "final_response" in result:
    print(f"Kết quả thảo luận nhóm: {result['final_response']}")
    print(f"Độ tin cậy: {result['confidence_score']}")
elif "response" in result:
    print(f"Phản hồi từ {result['role']}: {result['response']}")
```

### Thu thập phản hồi và tạo báo cáo

```python
# Thu thập phản hồi
score = assistant.feedback_manager.collect_feedback(
    query="Viết một hàm Python để tìm số Fibonacci",
    response=result["final_response"],
    model="group_discussion",
    is_group_discussion=True
)

# Lấy báo cáo hiệu suất
report = assistant.get_performance_report()

# Xuất dữ liệu RLHF
dataset_path = assistant.export_rlhf_dataset()
print(f"Đã xuất dataset RLHF tại: {dataset_path}")
```

### Tùy chỉnh quá trình tối ưu hóa

```python
# Tắt tối ưu hóa tự động
assistant.toggle_optimization(False)

# Tắt thu thập phản hồi
assistant.toggle_feedback_collection(False)

# Tắt tự động chọn mô hình
assistant.toggle_auto_select_model(False)

# Đặt lại trọng số tối ưu hóa
assistant.feedback_manager.reset_optimization(reset_feedback_db=False)

# Lấy trạng thái tối ưu hóa
status = assistant.get_optimization_status()
print(f"Trạng thái tối ưu hóa: {status['auto_optimization']}")
print(f"Trạng thái thu thập phản hồi: {status['feedback_enabled']}")
```

## Mở rộng hệ thống

### Thêm mô hình mới

```python
# Cập nhật file config/models.yml
new_model_config = {
    "name": "llama3:8b",
    "role": "general",
    "system_prompt": "Bạn là trợ lý thông minh và hữu ích.",
    "strengths": {
        "general_knowledge": 0.92,
        "language": 0.89,
        "reasoning": 0.85,
        "creative": 0.82,
        "problem_solving": 0.80
    }
}

# Tải lại cấu hình
config = AssistantFactory.load_config("config/models.yml")
assistant = setup_assistant(config)
```

### Tùy chỉnh thu thập phản hồi

```python
# Tùy chỉnh phương thức thu thập phản hồi
def custom_feedback_collector(query, response, score):
    # Lưu vào hệ thống của bạn
    your_system.save_feedback(query, response, score)
    
    # Sau đó thêm vào hệ thống RLHF
    assistant.feedback_manager.collect_feedback(
        query=query,
        response=response,
        model="your_model",
        score=score
    )

# Sử dụng collector tùy chỉnh
result = assistant.process_query("Hello world", collect_feedback=False)
custom_feedback_collector("Hello world", result["response"], 4.5)
```

### Tích hợp với web API

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
assistant = setup_assistant("config/default.yml")

@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    query = data.get('query')
    role = data.get('role')
    group_discussion = data.get('group_discussion', False)
    
    result = assistant.process_query(
        query=query,
        role=role,
        group_discussion=group_discussion,
        collect_feedback=False
    )
    
    return jsonify(result)

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    feedback_id = assistant.feedback_manager.collect_feedback(
        query=data['query'],
        response=data['response'],
        model=data['model'],
        score=data['score'],
        feedback_text=data.get('feedback_text'),
        is_group_discussion=data.get('is_group_discussion', False)
    )
    
    return jsonify({'success': True, 'feedback_id': feedback_id})

if __name__ == '__main__':
    app.run(port=8000)
```