#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务 - 处理AI模型配置和笔记生成
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# AI模型客户端
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AIService:
    """AI模型服务"""
    
    def __init__(self):
        self.config = Config()
        self.ai_config_file = self.config.BACKEND_DIR / 'config' / 'ai_config.json'
        self.ai_config = {}
        
        # 确保配置目录存在
        self.ai_config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载AI配置"""
        try:
            if self.ai_config_file.exists():
                with open(self.ai_config_file, 'r', encoding='utf-8') as f:
                    self.ai_config = json.load(f)
            else:
                # 创建默认配置
                self.ai_config = {
                    'provider': 'openai',
                    'api_key': '',
                    'model_name': 'gpt-3.5-turbo',
                    'base_url': '',
                    'max_tokens': 2000,
                    'temperature': 0.7,
                    'updated_at': datetime.now().isoformat()
                }
                self._save_config()
        except Exception as e:
            logger.error(f"加载AI配置失败: {e}")
            self.ai_config = {}
    
    def _save_config(self):
        """保存AI配置"""
        try:
            self.ai_config['updated_at'] = datetime.now().isoformat()
            with open(self.ai_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.ai_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存AI配置失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        # 返回配置副本，隐藏敏感信息
        config_copy = self.ai_config.copy()
        if 'api_key' in config_copy and config_copy['api_key']:
            # 只显示前4位和后4位
            api_key = config_copy['api_key']
            if len(api_key) > 8:
                config_copy['api_key'] = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        
        return config_copy
    
    def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """保存AI配置"""
        try:
            # 验证必要字段
            required_fields = ['provider', 'api_key', 'model_name']
            for field in required_fields:
                if field not in config:
                    return {
                        'success': False,
                        'message': f'缺少必要字段: {field}'
                    }
            
            # 验证提供商
            valid_providers = ['openai', 'anthropic', 'gemini', 'custom']
            if config['provider'] not in valid_providers:
                return {
                    'success': False,
                    'message': f'不支持的提供商: {config["provider"]}'
                }
            
            # 更新配置
            self.ai_config.update(config)
            self._save_config()
            
            return {
                'success': True,
                'message': 'AI配置保存成功'
            }
            
        except Exception as e:
            logger.error(f"保存AI配置失败: {e}")
            return {
                'success': False,
                'message': f'保存配置失败: {str(e)}'
            }
    
    def test_config(self) -> Dict[str, Any]:
        """测试AI配置"""
        try:
            if not self.ai_config.get('api_key'):
                return {
                    'success': False,
                    'message': 'API密钥未配置'
                }
            
            provider = self.ai_config.get('provider', 'openai')
            
            if provider == 'openai':
                return self._test_openai_config()
            elif provider == 'anthropic':
                return self._test_anthropic_config()
            elif provider == 'gemini':
                return self._test_gemini_config()
            elif provider == 'custom':
                return self._test_custom_config()
            else:
                return {
                    'success': False,
                    'message': f'不支持的提供商: {provider}'
                }
                
        except Exception as e:
            logger.error(f"测试AI配置失败: {e}")
            return {
                'success': False,
                'message': f'测试失败: {str(e)}'
            }
    
    def _test_openai_config(self) -> Dict[str, Any]:
        """测试OpenAI配置"""
        try:
            if openai is None:
                return {
                    'success': False,
                    'message': 'OpenAI库未安装'
                }
            
            # 配置OpenAI客户端
            client = openai.OpenAI(
                api_key=self.ai_config['api_key'],
                base_url=self.ai_config.get('base_url') or None
            )
            
            # 发送测试请求
            response = client.chat.completions.create(
                model=self.ai_config.get('model_name', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10
            )
            
            return {
                'success': True,
                'message': 'OpenAI配置测试成功',
                'response': response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'OpenAI测试失败: {str(e)}'
            }
    
    def _test_anthropic_config(self) -> Dict[str, Any]:
        """测试Anthropic配置"""
        try:
            if anthropic is None:
                return {
                    'success': False,
                    'message': 'Anthropic库未安装'
                }
            
            # 配置Anthropic客户端
            client = anthropic.Anthropic(
                api_key=self.ai_config['api_key']
            )
            
            # 发送测试请求
            response = client.messages.create(
                model=self.ai_config.get('model_name', 'claude-3-sonnet-20240229'),
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ]
            )
            
            return {
                'success': True,
                'message': 'Anthropic配置测试成功',
                'response': response.content[0].text
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Anthropic测试失败: {str(e)}'
            }
    
    def _test_gemini_config(self) -> Dict[str, Any]:
        """测试Gemini配置"""
        try:
            if genai is None:
                return {
                    'success': False,
                    'message': 'Google Generative AI库未安装'
                }
            
            # 配置Gemini
            genai.configure(api_key=self.ai_config['api_key'])
            
            # 创建模型
            model = genai.GenerativeModel(self.ai_config.get('model_name', 'gemini-pro'))
            
            # 发送测试请求
            response = model.generate_content("Hello, this is a test message.")
            
            return {
                'success': True,
                'message': 'Gemini配置测试成功',
                'response': response.text[:50] + '...' if len(response.text) > 50 else response.text
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Gemini测试失败: {str(e)}'
            }
    
    def _test_custom_config(self) -> Dict[str, Any]:
        """测试自定义配置"""
        try:
            if not self.ai_config.get('base_url'):
                return {
                    'success': False,
                    'message': '自定义提供商需要配置base_url'
                }
            
            # 使用OpenAI兼容的客户端
            if openai is None:
                return {
                    'success': False,
                    'message': 'OpenAI库未安装，无法测试自定义提供商'
                }
            
            client = openai.OpenAI(
                api_key=self.ai_config['api_key'],
                base_url=self.ai_config['base_url']
            )
            
            response = client.chat.completions.create(
                model=self.ai_config.get('model_name', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10
            )
            
            return {
                'success': True,
                'message': '自定义提供商配置测试成功',
                'response': response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'自定义提供商测试失败: {str(e)}'
            }
    
    def generate_notes(self, subtitle_text: str, custom_prompt: str = None, original_file_path: str = None, prompt_tag: str = None) -> Dict[str, Any]:
        """生成AI笔记"""
        try:
            if not self.ai_config.get('api_key'):
                return {
                    'success': False,
                    'message': 'AI配置未完成，请先配置API密钥'
                }
            
            if not subtitle_text.strip():
                return {
                    'success': False,
                    'message': '字幕内容为空'
                }
            
            # 构建提示词
            prompt = self._build_prompt(subtitle_text, custom_prompt)
            
            # 根据提供商生成笔记
            provider = self.ai_config.get('provider', 'openai')
            
            if provider == 'openai' or provider == 'custom':
                return self._generate_with_openai(prompt, original_file_path, prompt_tag)
            elif provider == 'anthropic':
                return self._generate_with_anthropic(prompt, original_file_path, prompt_tag)
            elif provider == 'gemini':
                return self._generate_with_gemini(prompt, original_file_path, prompt_tag)
            else:
                return {
                    'success': False,
                    'message': f'不支持的提供商: {provider}'
                }
                
        except Exception as e:
            logger.error(f"生成AI笔记失败: {e}")
            return {
                'success': False,
                'message': f'生成笔记失败: {str(e)}'
            }
    
    def _build_prompt(self, subtitle_text: str, custom_prompt: str = None) -> str:
        """构建提示词"""
        if custom_prompt:
            return f"{custom_prompt}\n\n以下是需要处理的字幕内容：\n{subtitle_text}"
        
        default_prompt = """
请根据以下字幕内容生成结构化的学习笔记。要求：

1. 提取主要观点和关键信息
2. 按逻辑顺序组织内容
3. 使用清晰的标题和子标题
4. 突出重要概念和术语
5. 如果有具体的步骤或方法，请列出详细步骤
6. 在适当的地方添加总结

请用中文输出，格式要清晰易读。

字幕内容：
"""
        
        return f"{default_prompt}\n{subtitle_text}"
    
    def _generate_with_openai(self, prompt: str, original_file_path: str = None, prompt_tag: str = None) -> Dict[str, Any]:
        """使用OpenAI生成笔记"""
        try:
            if openai is None:
                return {
                    'success': False,
                    'message': 'OpenAI库未安装'
                }
            
            client = openai.OpenAI(
                api_key=self.ai_config['api_key'],
                base_url=self.ai_config.get('base_url') or None
            )
            
            response = client.chat.completions.create(
                model=self.ai_config.get('model_name', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.ai_config.get('max_tokens', 2000),
                temperature=self.ai_config.get('temperature', 0.7)
            )
            
            notes_content = response.choices[0].message.content
            
            # 保存笔记文件
            notes_file = self._save_notes_file(notes_content, original_file_path, prompt_tag)
            
            return {
                'success': True,
                'message': '笔记生成成功',
                'notes_content': notes_content,
                'notes_file': notes_file,
                'model_used': self.ai_config.get('model_name', 'gpt-3.5-turbo'),
                'provider': 'openai'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'OpenAI生成失败: {str(e)}'
            }
    
    def _generate_with_anthropic(self, prompt: str, original_file_path: str = None, prompt_tag: str = None) -> Dict[str, Any]:
        """使用Anthropic生成笔记"""
        try:
            if anthropic is None:
                return {
                    'success': False,
                    'message': 'Anthropic库未安装'
                }
            
            client = anthropic.Anthropic(
                api_key=self.ai_config['api_key']
            )
            
            response = client.messages.create(
                model=self.ai_config.get('model_name', 'claude-3-sonnet-20240229'),
                max_tokens=self.ai_config.get('max_tokens', 2000),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            notes_content = response.content[0].text
            
            # 保存笔记文件
            notes_file = self._save_notes_file(notes_content, original_file_path, prompt_tag)
            
            return {
                'success': True,
                'message': '笔记生成成功',
                'notes_content': notes_content,
                'notes_file': notes_file,
                'model_used': self.ai_config.get('model_name', 'claude-3-sonnet-20240229'),
                'provider': 'anthropic'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Anthropic生成失败: {str(e)}'
            }
    
    def _generate_with_gemini(self, prompt: str, original_file_path: str = None, prompt_tag: str = None) -> Dict[str, Any]:
        """使用Gemini生成笔记"""
        try:
            if genai is None:
                return {
                    'success': False,
                    'message': 'Google Generative AI库未安装'
                }
            
            genai.configure(api_key=self.ai_config['api_key'])
            
            model = genai.GenerativeModel(self.ai_config.get('model_name', 'gemini-pro'))
            
            response = model.generate_content(prompt)
            
            notes_content = response.text
            
            # 保存笔记文件
            notes_file = self._save_notes_file(notes_content, original_file_path, prompt_tag)
            
            return {
                'success': True,
                'message': '笔记生成成功',
                'notes_content': notes_content,
                'notes_file': notes_file,
                'model_used': self.ai_config.get('model_name', 'gemini-pro'),
                'provider': 'gemini'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Gemini生成失败: {str(e)}'
            }
    
    def _save_notes_file(self, notes_content: str, original_file_path: str = None, prompt_tag: str = None) -> str:
        """保存笔记文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if original_file_path:
                # 使用源文件名称_时间格式
                from pathlib import Path
                original_name = Path(original_file_path).stem
                notes_filename = f"{original_name}_{timestamp}.md"
            else:
                # 兼容旧格式
                notes_filename = f"notes_{timestamp}.md"
                
            notes_path = self.config.OUTPUT_FOLDER / notes_filename
            
            # 在笔记内容开头插入提示词标识
            final_content = notes_content
            if prompt_tag:
                tag_line = f"<!-- PROMPT_TAG: {prompt_tag} -->\n\n"
                final_content = tag_line + notes_content
            
            with open(notes_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            logger.info(f"笔记文件保存成功: {notes_path}")
            return str(notes_path)
            
        except Exception as e:
            logger.error(f"保存笔记文件失败: {e}")
            return ""
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """获取可用的AI模型列表"""
        return {
            'openai': [
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k',
                'gpt-4',
                'gpt-4-turbo-preview',
                'gpt-4o',
                'gpt-4o-mini'
            ],
            'anthropic': [
                'claude-3-haiku-20240307',
                'claude-3-sonnet-20240229',
                'claude-3-opus-20240229',
                'claude-3-5-sonnet-20241022'
            ],
            'gemini': [
                'gemini-pro',
                'gemini-pro-vision',
                'gemini-1.5-pro',
                'gemini-1.5-flash'
            ]
        }