#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper服务 - 处理语音识别和字幕提取
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import tempfile

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None
    logging.warning("faster-whisper not installed, using mock implementation")

try:
    from ffmpy import FFmpeg
except ImportError:
    FFmpeg = None
    logging.warning("ffmpy not installed, audio preprocessing will be disabled")

from config import Config
from utils.file_utils import FileUtils
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WhisperService:
    """Whisper语音识别服务"""
    
    def __init__(self):
        self.config = Config()
        self.file_utils = FileUtils()
        self.current_model = None
        self.current_model_name = self.config.WHISPER_DEFAULT_MODEL
        self.model_config_file = self.config.BACKEND_DIR / 'config' / 'whisper_config.json'
        
        # 确保配置目录存在
        self.model_config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载Whisper配置"""
        try:
            if self.model_config_file.exists():
                with open(self.model_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_model_name = config.get('current_model', self.config.WHISPER_DEFAULT_MODEL)
                    # 加载字幕输出格式配置
                    subtitle_format = config.get('subtitle_output_format', self.config.SUBTITLE_OUTPUT_FORMAT)
                    if subtitle_format in self.config.SUBTITLE_AVAILABLE_FORMATS:
                        self.config.SUBTITLE_OUTPUT_FORMAT = subtitle_format
            else:
                self._save_config()
        except Exception as e:
            logger.error(f"加载Whisper配置失败: {e}")
            self.current_model_name = self.config.WHISPER_DEFAULT_MODEL
    
    def _save_config(self):
        """保存Whisper配置"""
        try:
            config = {
                'current_model': self.current_model_name,
                'subtitle_output_format': self.config.SUBTITLE_OUTPUT_FORMAT,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.model_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存Whisper配置失败: {e}")
    
    def _load_model(self, model_name: str) -> bool:
        """加载Whisper模型 - 优先使用本地模型"""
        try:
            if WhisperModel is None:
                logger.warning("faster-whisper未安装，使用模拟模式")
                return True
            
            # 如果当前模型已经是目标模型，直接返回
            if self.current_model and self.current_model_name == model_name:
                return True
            
            logger.info(f"正在加载Whisper模型: {model_name}")
            
            # 使用配置中的本地模型路径模板
            local_model_path = Path(str(self.config.WHISPER_LOCAL_MODEL_PATH_TEMPLATE).format(model_name=model_name))
            
            if local_model_path.exists() and local_model_path.is_dir():
                # 使用本地模型
                logger.info(f"使用本地模型: {local_model_path}")
                self.current_model = WhisperModel(
                    str(local_model_path),
                    device="cpu",
                    compute_type="int8"
                )
            else:
                # 下载模型到本地目录
                logger.info(f"下载模型到本地: {model_name} -> {self.config.WHISPER_MODEL_DIR}")
                # 确保模型目录存在
                self.config.WHISPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
                
                self.current_model = WhisperModel(
                    model_name,
                    device="cpu",
                    compute_type="int8",
                    download_root=str(self.config.WHISPER_MODEL_DIR)
                )
                
                logger.info(f"模型已下载到: {self.config.WHISPER_MODEL_DIR}")
            
            self.current_model_name = model_name
            self._save_config()
            
            logger.info(f"Whisper模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"加载Whisper模型失败: {e}")
            return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用的Whisper模型列表"""
        models = []
        
        for model_name in self.config.WHISPER_AVAILABLE_MODELS:
            model_info = {
                'name': model_name,
                'display_name': self._get_model_display_name(model_name),
                'size': self._get_model_size(model_name),
                'language': 'multilingual' if not model_name.endswith('.en') else 'english',
                'is_current': model_name == self.current_model_name,
                'is_downloaded': self._is_model_downloaded(model_name)
            }
            models.append(model_info)
        
        return models
    
    def _get_model_display_name(self, model_name: str) -> str:
        """获取模型显示名称"""
        display_names = {
            'base': 'Base (~74 MB)',
            'large-v3-turbo': 'Large v3 Turbo (~1550 MB)'
        }
        return display_names.get(model_name, model_name)
    
    def _get_model_size(self, model_name: str) -> str:
        """获取模型大小"""
        sizes = {
            'base': '74 MB',
            'large-v3-turbo': '1550 MB'
        }
        return sizes.get(model_name, 'Unknown')
    
    def _is_model_downloaded(self, model_name: str) -> bool:
        """检查模型是否已下载到本地"""
        try:
            # 检查本地模型路径
            local_model_path = Path(str(self.config.WHISPER_LOCAL_MODEL_PATH_TEMPLATE).format(model_name=model_name))
            
            # 检查模型目录是否存在且包含必要文件
            if local_model_path.exists() and local_model_path.is_dir():
                # 检查是否包含模型文件（通常包含config.json和model.bin等文件）
                required_files = ['config.json']
                for required_file in required_files:
                    if not (local_model_path / required_file).exists():
                        return False
                return True
            
            # 检查faster-whisper默认缓存目录
            import os
            cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
            if cache_dir.exists():
                # 查找包含模型名称的目录
                for item in cache_dir.iterdir():
                    if item.is_dir() and model_name in item.name.lower():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查模型下载状态失败: {e}")
            return False
    
    def get_current_model(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        return {
            'name': self.current_model_name,
            'display_name': self._get_model_display_name(self.current_model_name),
            'size': self._get_model_size(self.current_model_name),
            'is_loaded': self.current_model is not None
        }
    
    def select_model(self, model_name: str) -> Dict[str, Any]:
        """选择并加载Whisper模型"""
        try:
            if model_name not in self.config.WHISPER_AVAILABLE_MODELS:
                return {
                    'success': False,
                    'message': f'不支持的模型: {model_name}'
                }
            
            if self._load_model(model_name):
                return {
                    'success': True,
                    'message': f'模型切换成功: {model_name}',
                    'current_model': self.get_current_model()
                }
            else:
                return {
                    'success': False,
                    'message': f'模型加载失败: {model_name}'
                }
                
        except Exception as e:
            logger.error(f"选择模型失败: {e}")
            return {
                'success': False,
                'message': f'选择模型失败: {str(e)}'
            }
    
    def extract_subtitle(self, file_path: str, model_name: str = None, language: str = 'auto') -> Dict[str, Any]:
        """提取字幕"""
        preprocessed_file = None
        try:
            # 验证文件
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': '文件不存在'
                }
            
            # 选择模型
            if model_name and model_name != self.current_model_name:
                if not self._load_model(model_name):
                    return {
                        'success': False,
                        'message': f'模型加载失败: {model_name}'
                    }
            elif not self.current_model:
                if not self._load_model(self.current_model_name):
                    return {
                        'success': False,
                        'message': '默认模型加载失败'
                    }
            
            logger.info(f"开始提取字幕: {file_path}")
            
            if WhisperModel is None:
                # 模拟模式
                return self._mock_extract_subtitle(file_path)
            
            # 使用FFmpeg预处理音频
            logger.info("开始音频预处理...")
            preprocessed_file = self._preprocess_audio(file_path)
            
            # 执行转录（使用预处理后的文件）
            segments, info = self.current_model.transcribe(
                preprocessed_file,
                language=None if language == 'auto' else language,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            
            # 处理结果
            subtitle_segments = []
            full_text = ""
            
            for segment in segments:
                subtitle_segments.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip()
                })
                full_text += segment.text.strip() + " "
            
            # 保存字幕文件
            subtitle_file = self._save_subtitle_file(file_path, subtitle_segments)
            
            result = {
                'success': True,
                'message': '字幕提取成功',
                'subtitle_text': full_text.strip(),
                'segments': subtitle_segments,
                'subtitle_file': subtitle_file,
                'language': info.language,
                'duration': info.duration,
                'model_used': self.current_model_name
            }
            
            logger.info(f"字幕提取完成: {len(subtitle_segments)}个片段")
            return result
            
        except Exception as e:
            logger.error(f"字幕提取失败: {e}")
            return {
                'success': False,
                'message': f'字幕提取失败: {str(e)}'
            }
        finally:
            # 清理预处理产生的临时文件
            if preprocessed_file and preprocessed_file != file_path:
                self._cleanup_temp_file(preprocessed_file)
    
    def _mock_extract_subtitle(self, file_path: str) -> Dict[str, Any]:
        """模拟字幕提取（用于测试）"""
        mock_segments = [
            {'start': 0.0, 'end': 3.0, 'text': '这是一个测试字幕片段。'},
            {'start': 3.0, 'end': 6.0, 'text': '这里是第二个字幕片段。'},
            {'start': 6.0, 'end': 9.0, 'text': '最后一个测试片段。'}
        ]
        
        full_text = ' '.join([seg['text'] for seg in mock_segments])
        subtitle_file = self._save_subtitle_file(file_path, mock_segments)
        
        return {
            'success': True,
            'message': '字幕提取成功（模拟模式）',
            'subtitle_text': full_text,
            'segments': mock_segments,
            'subtitle_file': subtitle_file,
            'language': 'zh',
            'duration': 9.0,
            'model_used': self.current_model_name
        }
    
    def _preprocess_audio(self, input_path: str) -> str:
        """使用FFmpeg预处理音频文件
        
        Args:
            input_path: 输入音频/视频文件路径
            
        Returns:
            预处理后的MP3文件路径
        """
        if FFmpeg is None:
            logger.warning("FFmpeg未安装，跳过音频预处理")
            return input_path
            
        try:
            logger.info(f"开始音频预处理: {input_path}")
            
            # 创建项目内的Temp文件夹
            project_root = Path(__file__).parent.parent.parent  # 从backend/services回到项目根目录
            temp_dir = project_root / "Temp"
            temp_dir.mkdir(exist_ok=True)
            
            # 生成唯一的临时文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            temp_output = temp_dir / f"preprocessed_audio_{timestamp}.mp3"
            logger.debug(f"临时输出文件: {temp_output}")
            
            # 使用ffmpy构建FFmpeg命令：格式转换 + 降噪 + 音量标准化
            ff = FFmpeg(
                inputs={input_path: None},
                outputs={
                    str(temp_output): [
                        '-acodec', 'mp3',
                        '-ab', '128k',
                        '-ar', '16000',  # 采样率设为16kHz，适合语音识别
                        '-ac', '1',      # 单声道
                        # 音频滤镜：降噪 + 音量标准化
                        '-af', 'highpass=f=200,lowpass=f=3000,anlmdn=s=0.00001,loudnorm=I=-16:TP=-1.5:LRA=11',
                        '-y'  # 覆盖输出文件
                    ]
                }
            )
            
            logger.info(f"执行FFmpeg命令: {ff.cmd}")
            
            # 执行FFmpeg命令
            ff.run()
            
            # 检查输出文件是否存在
            if temp_output.exists():
                file_size = temp_output.stat().st_size
                logger.info(f"音频预处理成功完成: {temp_output} (文件大小: {file_size} bytes)")
                return str(temp_output)
            else:
                logger.error("FFmpeg执行完成但输出文件不存在")
                return input_path
            
        except Exception as e:
            logger.error(f"音频预处理失败，详细错误: {str(e)}")
            logger.exception("音频预处理异常堆栈:")
            return input_path
    
    def _cleanup_temp_file(self, file_path: str) -> None:
        """清理临时文件"""
        try:
            if not file_path or not os.path.exists(file_path):
                return
                
            file_path_obj = Path(file_path)
            project_root = Path(__file__).parent.parent.parent
            temp_dir = project_root / "Temp"
            
            # 只清理项目内Temp文件夹中的文件
            if temp_dir in file_path_obj.parents or file_path_obj.parent == temp_dir:
                os.remove(file_path)
                logger.debug(f"已清理临时文件: {file_path}")
                
                # 如果Temp文件夹为空，保留文件夹但清理内容
                try:
                    if temp_dir.exists() and not any(temp_dir.iterdir()):
                        logger.debug("Temp文件夹已清空")
                except:
                    pass
            else:
                logger.debug(f"跳过清理非项目临时文件: {file_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def _save_subtitle_file(self, original_file_path: str, segments: List[Dict]) -> str:
        """保存字幕文件"""
        try:
            # 获取输出格式
            output_format = self.config.SUBTITLE_OUTPUT_FORMAT.lower()
            if output_format not in self.config.SUBTITLE_AVAILABLE_FORMATS:
                output_format = 'vtt'  # 默认使用VTT格式
            
            # 生成字幕文件名
            original_name = Path(original_file_path).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            subtitle_filename = f"{original_name}_{timestamp}.{output_format}"
            subtitle_path = self.config.SUBTITLES_FOLDER / subtitle_filename
            
            # 根据格式生成内容
            if output_format == 'vtt':
                subtitle_content = self._generate_vtt_content(segments)
            else:  # srt
                subtitle_content = self._generate_srt_content(segments)
            
            # 保存文件
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(subtitle_content)
            
            logger.info(f"字幕文件保存成功: {subtitle_path} (格式: {output_format.upper()})")
            return str(subtitle_path)
            
        except Exception as e:
            logger.error(f"保存字幕文件失败: {e}")
            return ""
    
    def _generate_srt_content(self, segments: List[Dict]) -> str:
        """生成SRT格式内容"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_srt_time(segment['start'])
            end_time = self._seconds_to_srt_time(segment['end'])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{segment['text']}\n\n"
        
        return srt_content
    
    def _generate_vtt_content(self, segments: List[Dict]) -> str:
        """生成VTT格式内容"""
        vtt_content = "WEBVTT\n\n"
        
        for segment in segments:
            start_time = self._seconds_to_vtt_time(segment['start'])
            end_time = self._seconds_to_vtt_time(segment['end'])
            
            vtt_content += f"{start_time} --> {end_time}\n"
            vtt_content += f"{segment['text']}\n\n"
        
        return vtt_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """将秒数转换为VTT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"