#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置管理服务
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from models.ai_config import AIConfigModel
from services.ai_service import AIService
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIConfigService:
    """AI配置管理服务"""
    
    def __init__(self):
        # 数据库文件路径
        db_path = Path(__file__).parent.parent / 'data' / 'ai_configs.db'
        self.ai_config_model = AIConfigModel(str(db_path))
        self.ai_service = AIService()
        
        # 尝试从旧配置文件迁移数据
        self._migrate_from_old_config()
    
    def _migrate_from_old_config(self):
        """从旧的JSON配置文件迁移数据"""
        try:
            old_config_path = Path(__file__).parent.parent / 'ai_config.json'
            if old_config_path.exists():
                success = self.ai_config_model.migrate_from_json(str(old_config_path))
                if success:
                    logger.info("成功从旧配置文件迁移AI配置")
                    # 备份旧配置文件
                    backup_path = old_config_path.with_suffix('.json.backup')
                    old_config_path.rename(backup_path)
                    logger.info(f"旧配置文件已备份到: {backup_path}")
        except Exception as e:
            logger.warning(f"迁移旧配置文件失败: {e}")
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有AI配置"""
        try:
            configs = self.ai_config_model.get_all_configs()
            return {
                'success': True,
                'data': configs,
                'count': len(configs)
            }
        except Exception as e:
            logger.error(f"获取AI配置列表失败: {e}")
            return {
                'success': False,
                'message': f'获取配置列表失败: {str(e)}'
            }
    
    def get_config_by_id(self, config_id: int) -> Dict[str, Any]:
        """根据ID获取AI配置"""
        try:
            config = self.ai_config_model.get_config_by_id(config_id)
            if config:
                return {
                    'success': True,
                    'data': config
                }
            else:
                return {
                    'success': False,
                    'message': '配置不存在'
                }
        except Exception as e:
            logger.error(f"获取AI配置失败: {e}")
            return {
                'success': False,
                'message': f'获取配置失败: {str(e)}'
            }
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前使用的AI配置"""
        try:
            config = self.ai_config_model.get_current_config()
            if config:
                return {
                    'success': True,
                    'data': config
                }
            else:
                # 如果没有当前配置，返回默认配置结构
                return {
                    'success': True,
                    'data': {
                        'provider': 'openai',
                        'api_key': '',
                        'model_name': 'gpt-3.5-turbo',
                        'base_url': '',
                        'max_tokens': 2000,
                        'temperature': 0.7
                    }
                }
        except Exception as e:
            logger.error(f"获取当前AI配置失败: {e}")
            return {
                'success': False,
                'message': f'获取当前配置失败: {str(e)}'
            }
    
    def create_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新的AI配置"""
        try:
            # 验证必需字段
            required_fields = ['name', 'provider', 'api_key', 'model_name']
            for field in required_fields:
                if not config_data.get(field):
                    return {
                        'success': False,
                        'message': f'缺少必需字段: {field}'
                    }
            
            # 检查配置名称是否已存在
            existing_configs = self.ai_config_model.get_all_configs()
            for config in existing_configs:
                if config['name'] == config_data['name']:
                    return {
                        'success': False,
                        'message': '配置名称已存在'
                    }
            
            # 创建配置
            new_config = self.ai_config_model.create_config(config_data)
            
            logger.info(f"创建AI配置成功: {config_data['name']}")
            return {
                'success': True,
                'data': new_config,
                'message': '配置创建成功'
            }
            
        except Exception as e:
            logger.error(f"创建AI配置失败: {e}")
            return {
                'success': False,
                'message': f'创建配置失败: {str(e)}'
            }
    
    def update_config(self, config_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新AI配置"""
        try:
            # 验证必需字段
            required_fields = ['name', 'provider', 'api_key', 'model_name']
            for field in required_fields:
                if not config_data.get(field):
                    return {
                        'success': False,
                        'message': f'缺少必需字段: {field}'
                    }
            
            # 检查配置名称是否与其他配置冲突
            existing_configs = self.ai_config_model.get_all_configs()
            for config in existing_configs:
                if config['id'] != config_id and config['name'] == config_data['name']:
                    return {
                        'success': False,
                        'message': '配置名称已存在'
                    }
            
            # 更新配置
            updated_config = self.ai_config_model.update_config(config_id, config_data)
            
            if updated_config:
                logger.info(f"更新AI配置成功: {config_data['name']}")
                return {
                    'success': True,
                    'data': updated_config,
                    'message': '配置更新成功'
                }
            else:
                return {
                    'success': False,
                    'message': '配置不存在或更新失败'
                }
            
        except Exception as e:
            logger.error(f"更新AI配置失败: {e}")
            return {
                'success': False,
                'message': f'更新配置失败: {str(e)}'
            }
    
    def delete_config(self, config_id: int) -> Dict[str, Any]:
        """删除AI配置"""
        try:
            # 删除配置（允许删除当前配置）
            success = self.ai_config_model.delete_config(config_id)
            
            if success:
                logger.info(f"删除AI配置成功: ID {config_id}")
                return {
                    'success': True,
                    'message': '配置删除成功'
                }
            else:
                return {
                    'success': False,
                    'message': '配置不存在或删除失败'
                }
            
        except Exception as e:
            logger.error(f"删除AI配置失败: {e}")
            return {
                'success': False,
                'message': f'删除配置失败: {str(e)}'
            }
    
    def set_current_config(self, config_id: int) -> Dict[str, Any]:
        """设置当前使用的AI配置"""
        try:
            success = self.ai_config_model.set_current_config(config_id)
            
            if success:
                logger.info(f"设置当前AI配置成功: ID {config_id}")
                return {
                    'success': True,
                    'message': '当前配置设置成功'
                }
            else:
                return {
                    'success': False,
                    'message': '配置不存在或设置失败'
                }
            
        except Exception as e:
            logger.error(f"设置当前AI配置失败: {e}")
            return {
                'success': False,
                'message': f'设置当前配置失败: {str(e)}'
            }
    
    def test_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试AI配置连接"""
        # 临时保存当前配置
        original_config = self.ai_service.ai_config.copy()
        
        try:
            # 临时创建AI服务实例进行测试
            test_config = {
                'provider': config_data.get('provider', 'openai'),
                'api_key': config_data.get('api_key', ''),
                'model_name': config_data.get('model_name', 'gpt-3.5-turbo'),
                'base_url': config_data.get('base_url', ''),
                'max_tokens': config_data.get('max_tokens', 2000),
                'temperature': config_data.get('temperature', 0.7)
            }
            
            # 临时设置测试配置
            self.ai_service.ai_config = test_config
            
            # 使用AI服务的测试方法
            result = self.ai_service.test_config()
            
            return result
            
        except Exception as e:
            logger.error(f"测试AI配置失败: {e}")
            return {
                'success': False,
                'message': f'测试配置失败: {str(e)}'
            }
        finally:
            # 确保恢复原始配置
            try:
                self.ai_service.ai_config = original_config
            except Exception as restore_error:
                logger.error(f"恢复原始配置失败: {restore_error}")