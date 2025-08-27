#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 定义应用的基础配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
BACKEND_DIR = Path(__file__).parent

class Config:
    """基础配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_EXTENSIONS = {
        'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
    }
    
    # 允许的文件扩展名（扁平化列表）
    ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
    
    # 路径配置
    BASE_DIR = Path(__file__).parent.parent
    BACKEND_DIR = Path(__file__).parent
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or BASE_DIR / 'Output'
    SUBTITLES_FOLDER = os.environ.get('SUBTITLES_FOLDER') or BASE_DIR / 'Subtitles'
    PROMPTS_FOLDER = os.environ.get('PROMPTS_FOLDER') or BASE_DIR / 'Prompts'
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER') or BASE_DIR / 'Temp'
    WHISPER_MODELS_FOLDER = os.environ.get('WHISPER_MODELS_FOLDER') or BASE_DIR / 'Model'
    
    # Whisper配置 - 完全本地化
    WHISPER_MODEL_DIR = BASE_DIR / 'Model'  # 统一使用项目根目录下的Model文件夹
    WHISPER_DEFAULT_MODEL = 'base'
    WHISPER_AVAILABLE_MODELS = [
        'base', 'large-v3-turbo'  # 匹配实际存在的模型文件夹名称
    ]
    
    # 本地模型路径模板
    WHISPER_LOCAL_MODEL_PATH_TEMPLATE = WHISPER_MODEL_DIR / 'faster-whisper-{model_name}'
    
    # 字幕输出格式配置
    SUBTITLE_OUTPUT_FORMAT = os.environ.get('SUBTITLE_OUTPUT_FORMAT', 'vtt')  # 默认使用VTT格式
    SUBTITLE_AVAILABLE_FORMATS = ['srt', 'vtt']  # 支持的字幕格式
    
    # AI模型配置
    AI_CONFIG_FILE = BACKEND_DIR / 'config' / 'ai_config.json'
    
    # OpenAI配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Anthropic配置
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
    
    # Google Gemini配置
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-pro')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BACKEND_DIR / 'logs' / 'app.log'
    
    # 数据库配置（可选，用于历史记录）
    DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{BACKEND_DIR}/data/app.db')
    
    @classmethod
    def init_folders(cls):
        """初始化必要的文件夹"""
        folders = [
            cls.OUTPUT_FOLDER,
            cls.SUBTITLES_FOLDER,
            cls.PROMPTS_FOLDER,
            cls.TEMP_FOLDER,
            cls.WHISPER_MODEL_DIR,
            cls.AI_CONFIG_FILE.parent,
            cls.LOG_FILE.parent,
            Path(cls.DATABASE_URL.replace('sqlite:///', '')).parent
        ]
        
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_folder_paths(cls):
        """获取所有文件夹路径"""
        return {
            'output': str(cls.OUTPUT_FOLDER),
            'subtitles': str(cls.SUBTITLES_FOLDER),
            'prompts': str(cls.PROMPTS_FOLDER),
            'temp': str(cls.TEMP_FOLDER)
        }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# 初始化文件夹
Config.init_folders()