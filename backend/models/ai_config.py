#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置数据库模型
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class AIConfigModel:
    """AI配置数据库模型"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建AI配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    base_url TEXT,
                    max_tokens INTEGER DEFAULT 2000,
                    temperature REAL DEFAULT 0.7,
                    is_current BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_configs_name ON ai_configs(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_configs_is_current ON ai_configs(is_current)")
            
            conn.commit()
    
    def create_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 如果设置为当前配置，先取消其他配置的当前状态
            if config.get('is_current', False):
                cursor.execute("UPDATE ai_configs SET is_current = FALSE")
            
            # 插入新配置
            cursor.execute("""
                INSERT INTO ai_configs 
                (name, provider, api_key, model_name, base_url, max_tokens, temperature, is_current, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config['name'],
                config['provider'],
                config['api_key'],
                config['model_name'],
                config.get('base_url', ''),
                config.get('max_tokens', 2000),
                config.get('temperature', 0.7),
                config.get('is_current', False),
                datetime.now().isoformat()
            ))
            
            config_id = cursor.lastrowid
            conn.commit()
            
            return self.get_config_by_id(config_id)
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, provider, api_key, model_name, base_url, 
                       max_tokens, temperature, is_current, created_at, updated_at
                FROM ai_configs 
                ORDER BY is_current DESC, created_at DESC
            """)
            
            configs = []
            for row in cursor.fetchall():
                config = dict(row)
                # 隐藏API密钥的敏感信息
                if config['api_key']:
                    api_key = config['api_key']
                    if len(api_key) > 8:
                        config['api_key_masked'] = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
                    else:
                        config['api_key_masked'] = '*' * len(api_key)
                else:
                    config['api_key_masked'] = ''
                
                configs.append(config)
            
            return configs
    
    def get_config_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, provider, api_key, model_name, base_url, 
                       max_tokens, temperature, is_current, created_at, updated_at
                FROM ai_configs 
                WHERE id = ?
            """, (config_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_current_config(self) -> Optional[Dict[str, Any]]:
        """获取当前使用的AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, provider, api_key, model_name, base_url, 
                       max_tokens, temperature, is_current, created_at, updated_at
                FROM ai_configs 
                WHERE is_current = TRUE
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_config(self, config_id: int, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 如果设置为当前配置，先取消其他配置的当前状态
            if config.get('is_current', False):
                cursor.execute("UPDATE ai_configs SET is_current = FALSE")
            
            # 更新配置
            cursor.execute("""
                UPDATE ai_configs 
                SET name = ?, provider = ?, api_key = ?, model_name = ?, 
                    base_url = ?, max_tokens = ?, temperature = ?, is_current = ?, updated_at = ?
                WHERE id = ?
            """, (
                config['name'],
                config['provider'],
                config['api_key'],
                config['model_name'],
                config.get('base_url', ''),
                config.get('max_tokens', 2000),
                config.get('temperature', 0.7),
                config.get('is_current', False),
                datetime.now().isoformat(),
                config_id
            ))
            
            if cursor.rowcount > 0:
                conn.commit()
                return self.get_config_by_id(config_id)
            return None
    
    def delete_config(self, config_id: int) -> bool:
        """删除AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查是否为当前配置
            cursor.execute("SELECT is_current FROM ai_configs WHERE id = ?", (config_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            is_current = row[0]
            
            # 删除配置
            cursor.execute("DELETE FROM ai_configs WHERE id = ?", (config_id,))
            
            if cursor.rowcount > 0:
                # 如果删除的是当前配置，清除当前配置状态，不自动设置新的当前配置
                # 用户需要手动选择新的当前配置
                if is_current:
                    # 不需要额外操作，因为配置已被删除，is_current状态也随之清除
                    pass
                
                conn.commit()
                return True
            return False
    
    def set_current_config(self, config_id: int) -> bool:
        """设置当前使用的AI配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查配置是否存在
            cursor.execute("SELECT id FROM ai_configs WHERE id = ?", (config_id,))
            if not cursor.fetchone():
                return False
            
            # 取消所有配置的当前状态
            cursor.execute("UPDATE ai_configs SET is_current = FALSE")
            
            # 设置指定配置为当前配置
            cursor.execute("""
                UPDATE ai_configs 
                SET is_current = TRUE, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), config_id))
            
            conn.commit()
            return True
    
    def migrate_from_json(self, json_config_path: str) -> bool:
        """从JSON配置文件迁移数据"""
        try:
            json_path = Path(json_config_path)
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
            
            # 检查是否已有配置
            existing_configs = self.get_all_configs()
            if existing_configs:
                return False  # 已有配置，不进行迁移
            
            # 创建默认配置
            default_config = {
                'name': '默认配置',
                'provider': old_config.get('provider', 'openai'),
                'api_key': old_config.get('api_key', ''),
                'model_name': old_config.get('model_name', 'gpt-3.5-turbo'),
                'base_url': old_config.get('base_url', ''),
                'max_tokens': old_config.get('max_tokens', 2000),
                'temperature': old_config.get('temperature', 0.7),
                'is_current': True
            }
            
            self.create_config(default_config)
            return True
            
        except Exception as e:
            print(f"迁移配置失败: {e}")
            return False