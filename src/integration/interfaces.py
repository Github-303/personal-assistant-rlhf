"""
Giao diện chung cho hệ thống.
Cung cấp factory methods và các tiện ích để tạo và cấu hình các thành phần.
"""

import os
import logging
import yaml
from typing import Dict, Optional, Any

from src.core.models import ModelManager
from src.core.assistant import PersonalAssistant
from src.core.group_discussion import GroupDiscussionManager
from src.optimization.manager import FeedbackOptimizationManager
from src.integration.enhanced_assistant import EnhancedPersonalAssistant

logger = logging.getLogger(__name__)

class AssistantFactory:
    """Factory để tạo và cấu hình các đối tượng trợ lý."""
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Tải cấu hình từ file YAML.
        
        Args:
            config_path: Đường dẫn tới file cấu hình (None để sử dụng mặc định)
            
        Returns:
            Dict chứa cấu hình hệ thống
        """
        if config_path is None:
            config_dir = os.environ.get("CONFIG_DIR", "config")
            config_path = os.path.join(config_dir, "default.yml")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Tải các file cấu hình bổ sung
            config_dir = os.path.dirname(config_path)
            
            # Tải cấu hình mô hình
            models_path = os.path.join(config_dir, "models.yml")
            if os.path.exists(models_path):
                with open(models_path, 'r', encoding='utf-8') as f:
                    models_config = yaml.safe_load(f)
                if models_config:
                    config["models"] = models_config.get("models", [])
                    if "group_discussion" in models_config:
                        config["group_discussion"] = models_config["group_discussion"]
            
            # Tải cấu hình tối ưu hóa
            optimization_path = os.path.join(config_dir, "optimization.yml")
            if os.path.exists(optimization_path):
                with open(optimization_path, 'r', encoding='utf-8') as f:
                    optimization_config = yaml.safe_load(f)
                if optimization_config:
                    config["optimization"] = optimization_config
            
            # Thiết lập đường dẫn đến thư mục cấu hình
            if "system" not in config:
                config["system"] = {}
            config["system"]["config_dir"] = config_dir
            
            logger.info(f"Đã tải cấu hình từ {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Lỗi khi tải cấu hình từ {config_path}: {e}")
            # Trả về cấu hình tối thiểu
            return {
                "system": {
                    "version": "1.0.0",
                    "config_dir": config_dir if 'config_dir' in locals() else "config"
                }
            }
    
    @staticmethod
    def create_model_manager(config: Dict[str, Any]) -> ModelManager:
        """
        Tạo đối tượng quản lý mô hình.
        
        Args:
            config: Cấu hình hệ thống
            
        Returns:
            Đối tượng ModelManager đã được cấu hình
        """
        try:
            model_manager = ModelManager(config)
            return model_manager
        except Exception as e:
            logger.error(f"Lỗi khi tạo ModelManager: {e}")
            raise
    
    @staticmethod
    def create_base_assistant(config: Dict[str, Any], model_manager: ModelManager) -> PersonalAssistant:
        """
        Tạo đối tượng trợ lý cơ bản.
        
        Args:
            config: Cấu hình hệ thống
            model_manager: Đối tượng quản lý mô hình
            
        Returns:
            Đối tượng PersonalAssistant đã được cấu hình
        """
        try:
            assistant = PersonalAssistant(model_manager, config)
            return assistant
        except Exception as e:
            logger.error(f"Lỗi khi tạo PersonalAssistant: {e}")
            raise
    
    @staticmethod
    def create_group_discussion_manager(config: Dict[str, Any], model_manager: ModelManager) -> GroupDiscussionManager:
        """
        Tạo đối tượng quản lý thảo luận nhóm.
        
        Args:
            config: Cấu hình hệ thống
            model_manager: Đối tượng quản lý mô hình
            
        Returns:
            Đối tượng GroupDiscussionManager đã được cấu hình
        """
        try:
            group_manager = GroupDiscussionManager(model_manager, config)
            return group_manager
        except Exception as e:
            logger.error(f"Lỗi khi tạo GroupDiscussionManager: {e}")
            raise
    
    @staticmethod
    def create_feedback_optimization_manager(config: Dict[str, Any]) -> FeedbackOptimizationManager:
        """
        Tạo đối tượng quản lý tối ưu hóa phản hồi.
        
        Args:
            config: Cấu hình hệ thống
            
        Returns:
            Đối tượng FeedbackOptimizationManager đã được cấu hình
        """
        try:
            feedback_manager = FeedbackOptimizationManager(config)
            return feedback_manager
        except Exception as e:
            logger.error(f"Lỗi khi tạo FeedbackOptimizationManager: {e}")
            raise
    
    @staticmethod
    def create_enhanced_assistant(config: Dict[str, Any]) -> EnhancedPersonalAssistant:
        """
        Tạo đối tượng trợ lý nâng cao tích hợp tất cả các thành phần.
        
        Args:
            config: Cấu hình hệ thống
            
        Returns:
            Đối tượng EnhancedPersonalAssistant đã được cấu hình
        """
        try:
            # Tạo các thành phần cần thiết
            model_manager = AssistantFactory.create_model_manager(config)
            base_assistant = AssistantFactory.create_base_assistant(config, model_manager)
            group_manager = AssistantFactory.create_group_discussion_manager(config, model_manager)
            feedback_manager = AssistantFactory.create_feedback_optimization_manager(config)
            
            # Tạo trợ lý nâng cao
            enhanced_assistant = EnhancedPersonalAssistant(
                base_assistant=base_assistant,
                group_discussion_manager=group_manager,
                feedback_manager=feedback_manager,
                config=config
            )
            
            # Cấu hình tối ưu hóa
            optimization_config = config.get("optimization", {})
            if not optimization_config.get("enabled", True):
                enhanced_assistant.toggle_optimization(False)
            
            if not optimization_config.get("auto_select_model", True):
                enhanced_assistant.toggle_auto_select_model(False)
                
            feedback_config = optimization_config.get("feedback", {})
            if not feedback_config.get("enabled", True):
                enhanced_assistant.toggle_feedback_collection(False)
            
            logger.info("Đã tạo EnhancedPersonalAssistant thành công")
            return enhanced_assistant
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo EnhancedPersonalAssistant: {e}")
            raise


def setup_assistant(config_path: Optional[str] = None) -> EnhancedPersonalAssistant:
    """
    Hàm tiện ích để tạo và cấu hình trợ lý nâng cao.
    
    Args:
        config_path: Đường dẫn đến file cấu hình (None để sử dụng mặc định)
        
    Returns:
        Đối tượng EnhancedPersonalAssistant đã cấu hình
    """
    try:
        # Tải cấu hình
        config = AssistantFactory.load_config(config_path)
        
        # Tạo trợ lý nâng cao
        assistant = AssistantFactory.create_enhanced_assistant(config)
        
        return assistant
        
    except Exception as e:
        logger.error(f"Lỗi khi thiết lập assistant: {e}")
        raise