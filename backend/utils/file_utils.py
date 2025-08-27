#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具类 - 处理文件上传、验证、管理等操作
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import hashlib
import mimetypes
import logging

from config import Config
from .logger import setup_logger

logger = setup_logger(__name__)

class FileUtils:
    """文件处理工具类"""
    
    def __init__(self):
        self.config = Config()
        
        # 初始化必要的文件夹
        self._init_folders()
    
    def _init_folders(self):
        """初始化必要的文件夹"""
        folders = [
            self.config.OUTPUT_FOLDER,
            self.config.SUBTITLES_FOLDER,
            self.config.PROMPTS_FOLDER,
            self.config.TEMP_FOLDER,
            self.config.WHISPER_MODEL_DIR,
            self.config.BACKEND_DIR / 'config'
        ]
        
        for folder in folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                logger.debug(f"文件夹已创建或存在: {folder}")
            except Exception as e:
                logger.error(f"创建文件夹失败 {folder}: {e}")
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证文件"""
        try:
            if not os.path.exists(file_path):
                return {
                    'valid': False,
                    'message': '文件不存在'
                }
            
            file_size = os.path.getsize(file_path)
            if file_size > self.config.MAX_CONTENT_LENGTH:
                return {
                    'valid': False,
                    'message': f'文件大小超过限制 ({self._format_file_size(self.config.MAX_CONTENT_LENGTH)})'
                }
            
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.config.ALLOWED_EXTENSIONS:
                return {
                    'valid': False,
                    'message': f'不支持的文件格式: {file_ext}'
                }
            
            # 检查MIME类型
            mime_type, _ = mimetypes.guess_type(file_path)
            if not self._is_valid_mime_type(mime_type):
                return {
                    'valid': False,
                    'message': f'不支持的文件类型: {mime_type}'
                }
            
            return {
                'valid': True,
                'message': '文件验证通过',
                'file_info': {
                    'size': file_size,
                    'size_formatted': self._format_file_size(file_size),
                    'extension': file_ext,
                    'mime_type': mime_type,
                    'name': Path(file_path).name
                }
            }
            
        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            return {
                'valid': False,
                'message': f'文件验证失败: {str(e)}'
            }
    
    def _is_valid_mime_type(self, mime_type: str) -> bool:
        """检查MIME类型是否有效"""
        logger.info(f"检查MIME类型: {mime_type}")
        
        if not mime_type:
            logger.warning("MIME类型为空，但允许通过（可能是系统无法识别的文件类型）")
            return True  # 允许空MIME类型通过，依赖文件扩展名检查
        
        valid_mime_types = [
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/wmv',
            'video/flv', 'video/webm', 'video/m4v', 'video/3gp', 'video/quicktime',
            'video/x-msvideo', 'video/x-ms-wmv', 'video/x-flv',
            'audio/mp3', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg',
            'audio/m4a', 'audio/wma', 'audio/mpeg', 'audio/x-wav', 'audio/mp4'
        ]
        
        # 检查是否为视频或音频类型（更宽松的检查）
        is_video_audio = mime_type.startswith('video/') or mime_type.startswith('audio/')
        is_in_list = mime_type in valid_mime_types
        
        result = is_in_list or is_video_audio
        logger.info(f"MIME类型检查结果: {mime_type} -> {result} (在列表中: {is_in_list}, 是视频/音频: {is_video_audio})")
        
        return result
    
    def save_uploaded_file(self, file_data: bytes, filename: str, timestamp: str = None) -> Dict[str, Any]:
        """保存上传的文件"""
        try:
            # 生成安全的文件名
            safe_filename = self._generate_safe_filename(filename)
            
            # 生成文件路径，使用传入的timestamp或生成新的
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 正确处理文件名和扩展名
            name_part, ext_part = os.path.splitext(safe_filename)
            final_filename = f"{name_part}_{timestamp}{ext_part}"
            file_path = self.config.TEMP_FOLDER / final_filename
            
            logger.info(f"开始保存文件: {filename} -> {file_path}")
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"文件写入完成: {file_path}, 大小: {len(file_data)} bytes")
            
            # 验证保存的文件
            validation_result = self.validate_file(str(file_path))
            if not validation_result['valid']:
                # 记录详细的验证失败信息，但不立即删除文件
                logger.warning(f"文件验证失败: {file_path}, 原因: {validation_result['message']}")
                logger.warning(f"文件将保留以供调试，请手动检查文件内容")
                return {
                    'success': False,
                    'message': validation_result['message'],
                    'file_path': str(file_path)  # 返回文件路径以供调试
                }
            
            logger.info(f"文件保存并验证成功: {file_path}")
            return {
                'success': True,
                'message': '文件保存成功',
                'file_path': str(file_path),
                'file_info': validation_result['file_info']
            }
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return {
                'success': False,
                'message': f'保存文件失败: {str(e)}'
            }
    
    def _generate_safe_filename(self, filename: str) -> str:
        """生成安全的文件名"""
        # 移除路径分隔符和特殊字符
        safe_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # 确保文件名不为空
        if not safe_filename:
            safe_filename = "uploaded_file"
        
        # 限制文件名长度
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:95] + ext
        
        return safe_filename
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在: {file_path}")
                return False
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def move_file(self, src_path: str, dst_path: str) -> bool:
        """移动文件"""
        try:
            # 确保目标目录存在
            dst_dir = Path(dst_path).parent
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.move(src_path, dst_path)
            logger.info(f"文件移动成功: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"移动文件失败: {e}")
            return False
    
    def copy_file(self, src_path: str, dst_path: str) -> bool:
        """复制文件"""
        try:
            # 确保目标目录存在
            dst_dir = Path(dst_path).parent
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, dst_path)
            logger.info(f"文件复制成功: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return False
    
    def get_file_hash(self, file_path: str, algorithm: str = 'md5') -> Optional[str]:
        """计算文件哈希值"""
        try:
            hash_func = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def clean_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """清理临时文件"""
        try:
            deleted_count = 0
            total_size = 0
            current_time = datetime.now()
            
            for file_path in self.config.TEMP_FOLDER.glob('*'):
                if file_path.is_file():
                    # 检查文件年龄
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        file_size = file_path.stat().st_size
                        if self.delete_file(str(file_path)):
                            deleted_count += 1
                            total_size += file_size
            
            return {
                'success': True,
                'message': f'清理完成，删除了 {deleted_count} 个文件',
                'deleted_count': deleted_count,
                'freed_space': self._format_file_size(total_size)
            }
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            return {
                'success': False,
                'message': f'清理失败: {str(e)}'
            }
    
    def get_folder_info(self, folder_path: str) -> Dict[str, Any]:
        """获取文件夹信息"""
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return {
                    'exists': False,
                    'message': '文件夹不存在'
                }
            
            file_count = 0
            total_size = 0
            
            for file_path in folder.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
            
            return {
                'exists': True,
                'path': str(folder),
                'file_count': file_count,
                'total_size': total_size,
                'total_size_formatted': self._format_file_size(total_size)
            }
            
        except Exception as e:
            logger.error(f"获取文件夹信息失败: {e}")
            return {
                'exists': False,
                'message': f'获取信息失败: {str(e)}'
            }
    
    def list_files(self, folder_path: str, pattern: str = '*', recursive: bool = False) -> List[Dict[str, Any]]:
        """列出文件夹中的文件"""
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return []
            
            files = []
            search_func = folder.rglob if recursive else folder.glob
            
            for file_path in search_func(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'size_formatted': self._format_file_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': file_path.suffix.lower()
                    })
            
            # 按修改时间排序（最新的在前）
            files.sort(key=lambda x: x['modified'], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    def get_folder_paths(self) -> Dict[str, str]:
        """获取所有文件夹路径"""
        return {
            'output': str(self.config.OUTPUT_FOLDER),
            'subtitles': str(self.config.SUBTITLES_FOLDER),
            'prompts': str(self.config.PROMPTS_FOLDER),
            'temp': str(self.config.TEMP_FOLDER),
            'whisper_models': str(self.config.WHISPER_MODEL_DIR)
        }
    
    def find_file_by_id(self, file_id: str) -> Optional[str]:
        """根据file_id在Temp文件夹中查找对应的文件"""
        try:
            # file_id格式: filename_timestamp (不含扩展名)
            # 实际文件名格式: filename_timestamp.ext
            logger.info(f"查找file_id对应的文件: {file_id}")
            
            # 精确匹配：查找以file_id开头且后面跟扩展名的文件
            for file_path in self.config.TEMP_FOLDER.glob('*'):
                if file_path.is_file():
                    # 获取文件名（不含扩展名）
                    filename_without_ext = file_path.stem
                    # 精确匹配file_id
                    if filename_without_ext == file_id:
                        logger.info(f"精确匹配找到文件: {file_id} -> {file_path}")
                        return str(file_path)
            
            # 如果精确匹配失败，尝试模糊匹配（向后兼容）
            logger.warning(f"精确匹配失败，尝试模糊匹配: {file_id}")
            for file_path in self.config.TEMP_FOLDER.glob('*'):
                if file_path.is_file():
                    filename_without_ext = file_path.stem
                    # 检查file_id是否是文件名的前缀
                    if filename_without_ext.startswith(file_id):
                        logger.info(f"模糊匹配找到文件: {file_id} -> {file_path}")
                        return str(file_path)
            
            logger.warning(f"未找到file_id对应的文件: {file_id}")
            # 列出当前temp文件夹中的所有文件以便调试
            temp_files = [f.name for f in self.config.TEMP_FOLDER.glob('*') if f.is_file()]
            logger.info(f"当前temp文件夹中的文件: {temp_files}")
            return None
            
        except Exception as e:
            logger.error(f"根据file_id查找文件失败: {e}")
            return None