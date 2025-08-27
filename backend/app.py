#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音视频AI笔记生成软件 - Flask后端主应用
"""

import os
import sys
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入自定义模块
from config import Config
from services.whisper_service import WhisperService
from services.ai_service import AIService
# from services.subtitle_service import SubtitleService
from services.ai_config_service import AIConfigService
from utils.file_utils import FileUtils
from utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 启用CORS
    CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'])
    
    # 初始化服务
    whisper_service = WhisperService()
    ai_service = AIService()
    # subtitle_service = SubtitleService()
    ai_config_service = AIConfigService()
    file_utils = FileUtils()
    
    # 添加请求日志中间件
    @app.before_request
    def log_request_info():
        """记录请求开始信息"""
        request.start_time = time.time()
        logger.info(f"[REQUEST] {request.method} {request.url} - IP: {request.remote_addr} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
        if request.is_json and request.get_json():
            logger.info(f"[REQUEST BODY] {request.get_json()}")
    
    @app.after_request
    def log_response_info(response):
        """记录请求结束信息"""
        duration = round((time.time() - getattr(request, 'start_time', time.time())) * 1000, 2)
        logger.info(f"[RESPONSE] {request.method} {request.url} - Status: {response.status_code} - Duration: {duration}ms")
        return response
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """文件上传接口"""
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'msg': '没有文件被上传'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'msg': '没有选择文件'
                }), 400
            
            # 保存文件
            filename = secure_filename(file.filename)
            file_data = file.read()
            
            # 生成统一的时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 使用FileUtils保存并验证文件，传入时间戳确保一致性
            result = file_utils.save_uploaded_file(file_data, filename, timestamp)
            
            if not result['success']:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 400
            
            # 生成file_id用于后续操作，使用相同的时间戳
            file_id = os.path.splitext(filename)[0] + '_' + timestamp
            
            logger.info(f"文件上传成功: {filename}")
            return jsonify({
                'success': True,
                'data': {
                    'file_id': file_id,
                    'filename': filename,
                    'file_path': result['file_path'],
                    'file_size': result['file_info'].get('size', 0),
                    'duration': result['file_info'].get('duration')
                },
                'msg': '文件上传成功'
            })
            
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'文件上传失败: {str(e)}'
            }), 500
    
    @app.route('/api/delete-file', methods=['DELETE'])
    def delete_file():
        """删除文件接口"""
        try:
            data = request.get_json()
            file_id = data.get('file_id')
            
            if not file_id:
                return jsonify({
                    'success': False,
                    'msg': '文件ID不能为空'
                }), 400
            
            # 根据file_id查找文件路径
            file_path = file_utils.find_file_by_id(file_id)
            if not file_path:
                return jsonify({
                    'success': False,
                    'msg': f'未找到file_id对应的文件: {file_id}'
                }), 400
            
            # 删除文件
            success = file_utils.delete_file(file_path)
            
            if success:
                logger.info(f"文件删除成功: {file_path}")
                return jsonify({
                    'success': True,
                    'msg': '文件删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': '文件删除失败'
                }), 500
                
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'文件删除失败: {str(e)}'
            }), 500
    
    @app.route('/api/extract-subtitle', methods=['POST'])
    def extract_subtitle():
        """字幕提取接口"""
        try:
            data = request.get_json()
            file_path = data.get('file_path')
            file_id = data.get('file_id')
            model_name = data.get('model_name', 'base')
            language = data.get('language', 'auto')
            
            # 支持file_id和file_path两种参数
            if file_id:
                # 根据file_id查找文件路径
                file_path = file_utils.find_file_by_id(file_id)
                if not file_path:
                    return jsonify({
                        'success': False,
                        'msg': f'未找到file_id对应的文件: {file_id}'
                    }), 400
            elif file_path:
                # 直接使用file_path
                if not os.path.exists(file_path):
                    return jsonify({
                        'success': False,
                        'msg': '文件不存在'
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'msg': '请提供file_id或file_path参数'
                }), 400
            
            # 提取字幕
            result = whisper_service.extract_subtitle(
                file_path=file_path,
                model_name=model_name,
                language=language
            )
            
            # 统一返回格式
            if result.get('success', True):  # whisper_service可能返回不同格式
                logger.info(f"字幕提取成功: {file_path}")
                return jsonify({
                    'success': True,
                    'data': {
                        'subtitle_text': result.get('subtitle_text', result.get('text', '')),
                        'subtitle_file': result.get('subtitle_file', ''),
                        'file_path': file_path,
                        'model_name': model_name
                    },
                    'msg': '字幕提取成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result.get('message', '字幕提取失败')
                }), 500
            
        except Exception as e:
            logger.error(f"字幕提取失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'字幕提取失败: {str(e)}'
            }), 500
    
    @app.route('/api/generate-note', methods=['POST'])
    def generate_note():
        """AI笔记生成接口"""
        try:
            data = request.get_json()
            subtitle_text = data.get('subtitle_text')
            prompt = data.get('prompt', '')  # 统一参数名为prompt
            original_file_path = data.get('original_file_path')  # 原始文件路径
            prompt_tag = data.get('prompt_tag', '')  # 提示词标识
            
            if not subtitle_text:
                return jsonify({
                    'success': False,
                    'msg': '字幕文本不能为空'
                }), 400
            
            # 生成笔记
            result = ai_service.generate_notes(
                subtitle_text=subtitle_text,
                custom_prompt=prompt,
                original_file_path=original_file_path,
                prompt_tag=prompt_tag
            )
            
            # 统一返回格式
            if result.get('success', False):
                logger.info("AI笔记生成成功")
                return jsonify({
                    'success': True,
                    'data': {
                        'note_content': result.get('notes_content', ''),  # AI服务返回notes_content
                        'note_file': result.get('notes_file', '')        # AI服务返回notes_file
                    },
                    'msg': '笔记生成成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result.get('message', '笔记生成失败')
                }), 500
            
        except Exception as e:
            logger.error(f"AI笔记生成失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'AI笔记生成失败: {str(e)}'
            }), 500
    
    @app.route('/api/whisper/models', methods=['GET'])
    def get_whisper_models():
        """获取Whisper模型列表"""
        try:
            models = whisper_service.get_available_models()
            return jsonify({
                'success': True,
                'data': models,
                'msg': '获取模型列表成功'
            })
        except Exception as e:
            logger.error(f"获取Whisper模型列表失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'获取模型列表失败: {str(e)}'
            }), 500
    
    @app.route('/api/whisper/models/current', methods=['GET'])
    def get_current_whisper_model():
        """获取当前Whisper模型"""
        try:
            current_model = whisper_service.get_current_model()
            return jsonify({'current_model': current_model})
        except Exception as e:
            logger.error(f"获取当前Whisper模型失败: {str(e)}")
            return jsonify({'error': f'获取当前模型失败: {str(e)}'}), 500
    
    @app.route('/api/whisper/models/select', methods=['POST'])
    def select_whisper_model():
        """选择Whisper模型"""
        try:
            data = request.get_json()
            model_name = data.get('model_name')
            
            if not model_name:
                return jsonify({'error': '模型名称不能为空'}), 400
            
            result = whisper_service.select_model(model_name)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"选择Whisper模型失败: {str(e)}")
            return jsonify({'error': f'选择模型失败: {str(e)}'}), 500
    
    @app.route('/api/ai/config', methods=['GET'])
    def get_ai_config():
        """获取AI配置"""
        try:
            config = ai_service.get_config()
            return jsonify(config)
        except Exception as e:
            logger.error(f"获取AI配置失败: {str(e)}")
            return jsonify({'error': f'获取AI配置失败: {str(e)}'}), 500
    
    @app.route('/api/ai/config', methods=['POST'])
    def save_ai_config():
        """保存AI配置"""
        try:
            data = request.get_json()
            result = ai_service.save_config(data)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"保存AI配置失败: {str(e)}")
            return jsonify({'error': f'保存AI配置失败: {str(e)}'}), 500
    
    @app.route('/api/ai/test', methods=['POST'])
    def test_ai_config():
        """测试AI配置"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据为空'
                }), 400
            
            # 使用新的AI配置服务测试
            result = ai_config_service.test_config(data)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"测试AI配置失败: {e}")
            return jsonify({
                'success': False,
                'message': f'测试失败: {str(e)}'
            }), 500

    # 新的AI配置管理API
    @app.route('/api/ai/configs', methods=['GET'])
    def get_ai_configs():
        """获取所有AI配置"""
        try:
            result = ai_config_service.get_all_configs()
            if result['success']:
                return jsonify({
                    'success': True,
                    'data': result['data'],
                    'msg': '获取配置成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 500
        except Exception as e:
            logger.error(f"获取AI配置失败: {e}")
            return jsonify({
                'success': False,
                'msg': f'获取配置失败: {str(e)}'
            }), 500

    @app.route('/api/ai/configs', methods=['POST'])
    def create_ai_config():
        """创建AI配置"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'msg': '请求数据为空'
                }), 400
            
            result = ai_config_service.create_config(data)
            if result['success']:
                return jsonify({
                    'success': True,
                    'data': result['data'],
                    'msg': result['message']
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 400
        except Exception as e:
            logger.error(f"创建AI配置失败: {e}")
            return jsonify({
                'success': False,
                'msg': f'创建配置失败: {str(e)}'
            }), 500

    @app.route('/api/ai/configs/<int:config_id>', methods=['PUT'])
    def update_ai_config(config_id):
        """更新AI配置"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'msg': '请求数据为空'
                }), 400
            
            result = ai_config_service.update_config(config_id, data)
            if result['success']:
                return jsonify({
                    'success': True,
                    'data': result['data'],
                    'msg': result['message']
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 400
        except Exception as e:
            logger.error(f"更新AI配置失败: {e}")
            return jsonify({
                'success': False,
                'msg': f'更新配置失败: {str(e)}'
            }), 500

    @app.route('/api/ai/configs/<int:config_id>', methods=['DELETE'])
    def delete_ai_config(config_id):
        """删除AI配置"""
        try:
            result = ai_config_service.delete_config(config_id)
            if result['success']:
                return jsonify({
                    'success': True,
                    'msg': result['message']
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 400
        except Exception as e:
            logger.error(f"删除AI配置失败: {e}")
            return jsonify({
                'success': False,
                'msg': f'删除配置失败: {str(e)}'
            }), 500

    @app.route('/api/ai/configs/<int:config_id>/set-current', methods=['POST'])
    def set_current_ai_config(config_id):
        """设置当前AI配置"""
        try:
            result = ai_config_service.set_current_config(config_id)
            if result['success']:
                return jsonify({
                    'success': True,
                    'msg': result['message']
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 400
        except Exception as e:
            logger.error(f"设置当前AI配置失败: {e}")
            return jsonify({
                'success': False,
                'msg': f'设置当前配置失败: {str(e)}'
            }), 500

    @app.route('/api/ai/configs/current', methods=['GET'])
    def get_current_ai_config():
        """获取当前AI配置"""
        try:
            result = ai_config_service.get_current_config()
            if result['success']:
                return jsonify({
                    'success': True,
                    'data': result['data'],
                    'msg': '获取当前配置成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'msg': result['message']
                }), 404
        except Exception as e:
            logger.error(f"获取当前AI配置失败: {e}")
            return jsonify({
                'success': False,
                'msg': f'获取当前配置失败: {str(e)}'
            }), 500
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """获取系统配置"""
        try:
            config_data = {
                'whisper_models': whisper_service.get_available_models(),
                'current_whisper_model': whisper_service.get_current_model(),
                'ai_config': ai_service.get_config(),
                'upload_settings': {
                    'max_file_size': Config.MAX_CONTENT_LENGTH,
                    'allowed_extensions': Config.ALLOWED_EXTENSIONS
                }
            }
            return jsonify({
                'success': True,
                'data': config_data,
                'msg': '获取配置成功'
            })
        except Exception as e:
            logger.error(f"获取系统配置失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'获取配置失败: {str(e)}'
            }), 500
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        """更新系统配置"""
        try:
            data = request.get_json()
            
            # 更新AI配置
            if 'ai_config' in data:
                ai_service.save_config(data['ai_config'])
            
            # 更新Whisper模型
            if 'whisper_model' in data:
                whisper_service.select_model(data['whisper_model'])
            
            return jsonify({
                'success': True,
                'msg': '配置更新成功'
            })
            
        except Exception as e:
            logger.error(f"更新系统配置失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'配置更新失败: {str(e)}'
            }), 500
    
    @app.route('/api/notes/history', methods=['GET'])
    def get_notes_history():
        """获取历史笔记列表"""
        try:
            notes_files = file_utils.list_files(
                folder_path=str(Config.OUTPUT_FOLDER),
                pattern='*.md',
                recursive=False
            )
            
            # 按修改时间倒序排列
            notes_files.sort(key=lambda x: x['modified'], reverse=True)
            
            return jsonify({
                'success': True,
                'data': notes_files,
                'count': len(notes_files)
            })
            
        except Exception as e:
            logger.error(f"获取历史笔记失败: {str(e)}")
            return jsonify({'error': f'获取历史笔记失败: {str(e)}'}), 500
    
    @app.route('/api/notes/<filename>', methods=['GET'])
    def get_note_content(filename):
        """获取笔记内容"""
        try:
            file_path = Config.OUTPUT_FOLDER / filename
            if not file_path.exists():
                return jsonify({'error': '笔记文件不存在'}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'filename': filename,
                'content': content,
                'file_path': str(file_path)
            })
            
        except Exception as e:
            logger.error(f"获取笔记内容失败: {str(e)}")
            return jsonify({'error': f'获取笔记内容失败: {str(e)}'}), 500
    
    @app.route('/api/prompts', methods=['GET'])
    def get_prompts():
        """获取提示词文件列表"""
        try:
            prompts_folder = Path('d:/Projects/self-projects/self-projects/video-note/Prompts')
            if not prompts_folder.exists():
                return jsonify({
                    'success': False,
                    'msg': 'Prompts文件夹不存在'
                }), 404
            
            prompts = []
            for file_path in prompts_folder.glob('*.txt'):
                prompts.append({
                    'name': file_path.stem,
                    'filename': file_path.name,
                    'path': str(file_path)
                })
            
            # 确保default_note_prompt在第一位
            prompts.sort(key=lambda x: (x['name'] != 'default_note_prompt', x['name']))
            
            return jsonify({
                'success': True,
                'data': prompts,
                'count': len(prompts)
            })
            
        except Exception as e:
            logger.error(f"获取提示词列表失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'获取提示词列表失败: {str(e)}'
            }), 500
    
    @app.route('/api/subtitles', methods=['GET'])
    def get_subtitles():
        """获取已解析字幕文件列表"""
        try:
            # 支持多种字幕格式
            subtitle_extensions = ['*.srt', '*.vtt', '*.ass', '*.ssa', '*.sub', '*.sbv', '*.lrc', '*.ttml', '*.dfxp']
            all_subtitles = []
            
            for pattern in subtitle_extensions:
                subtitles_files = file_utils.list_files(
                    folder_path=str(Config.SUBTITLES_FOLDER),
                    pattern=pattern,
                    recursive=False
                )
                all_subtitles.extend(subtitles_files)
            
            # 按修改时间倒序排列
            all_subtitles.sort(key=lambda x: x['modified'], reverse=True)
            
            return jsonify({
                'success': True,
                'data': all_subtitles,
                'count': len(all_subtitles)
            })
            
        except Exception as e:
            logger.error(f"获取字幕文件列表失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'获取字幕文件列表失败: {str(e)}'
            }), 500
    
    @app.route('/api/subtitles/<filename>', methods=['GET'])
    def get_subtitle_content(filename):
        """获取字幕文件内容"""
        try:
            file_path = Config.SUBTITLES_FOLDER / filename
            if not file_path.exists():
                return jsonify({
                    'success': False,
                    'msg': '字幕文件不存在'
                }), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'filename': filename,
                'content': content,
                'file_path': str(file_path)
            })
            
        except Exception as e:
            logger.error(f"获取字幕内容失败: {str(e)}")
            return jsonify({
                'success': False,
                'msg': f'获取字幕内容失败: {str(e)}'
            }), 500
    
    @app.route('/api/files/download/<path:filename>', methods=['GET'])
    def download_file(filename):
        """文件下载接口"""
        try:
            file_path = file_utils.get_download_path(filename)
            if not os.path.exists(file_path):
                return jsonify({'error': '文件不存在'}), 404
            
            return send_file(file_path, as_attachment=True)
            
        except Exception as e:
            logger.error(f"文件下载失败: {str(e)}")
            return jsonify({'error': f'文件下载失败: {str(e)}'}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '接口不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': '服务器内部错误'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )