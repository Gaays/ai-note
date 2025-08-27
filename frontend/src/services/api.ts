import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  // 移除timeout限制，支持长音视频字幕解析（可能超过5分钟）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// API接口定义
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  msg: string
}

export interface FileUploadResponse {
  file_id: string
  filename: string
  file_path: string
  file_size: number
  duration?: number
}

export interface SubtitleExtractionResponse {
  subtitle_text: string
  subtitle_file: string
  segments: Array<{
    start: number
    end: number
    text: string
  }>
}

export interface NoteGenerationResponse {
  note_content: string
  note_file: string
}

export interface WhisperModel {
  name: string
  size: string
  path: string
  is_current: boolean
}

export interface AIModelConfig {
  id?: number
  name: string
  provider: string
  api_key: string
  model_name: string
  base_url?: string
  is_current?: boolean
  created_at?: string
  updated_at?: string
}

export interface HistoryNote {
  name: string
  path: string
  size: number
  size_formatted: string
  modified: string
  extension: string
}

export interface NoteContentResponse {
  content: string
  filename: string
}

export interface PromptFile {
  name: string
  filename: string
  path: string
}

export interface SubtitleFile {
  name: string
  path: string
  size: number
  size_formatted: string
  modified: string
  extension: string
}

export interface SubtitleContentResponse {
  content: string
  filename: string
  file_path: string
}

// API方法
export const apiService = {
  // 文件上传
  uploadFile: (file: File): Promise<ApiResponse<FileUploadResponse>> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除文件
  deleteFile: (fileId: string): Promise<ApiResponse> => {
    return api.delete('/delete-file', {
      data: { file_id: fileId }
    })
  },

  // 字幕提取
  extractSubtitle: (fileId: string, modelName?: string): Promise<ApiResponse<SubtitleExtractionResponse>> => {
    return api.post('/extract-subtitle', {
      file_id: fileId,
      model_name: modelName
    })
  },

  // AI笔记生成
  generateNote: (subtitleText: string, prompt?: string, originalFilePath?: string, promptTag?: string): Promise<ApiResponse<NoteGenerationResponse>> => {
    return api.post('/generate-note', {
      subtitle_text: subtitleText,
      prompt: prompt,
      original_file_path: originalFilePath,
      prompt_tag: promptTag
    })
  },

  // 获取Whisper模型列表
  getWhisperModels: (): Promise<ApiResponse<WhisperModel[]>> => {
    return api.get('/whisper/models')
  },

  // 选择Whisper模型
  selectWhisperModel: (modelName: string): Promise<ApiResponse> => {
    return api.post('/whisper/models/select', {
      model_name: modelName
    })
  },

  // 获取AI模型配置
  getAIConfig: (): Promise<ApiResponse<AIModelConfig>> => {
    return api.get('/ai/config')
  },

  // 更新AI模型配置
  updateAIConfig: (config: AIModelConfig): Promise<ApiResponse> => {
    return api.post('/ai/config', config)
  },

  // 测试AI连接
  testAIConnection: (config?: AIModelConfig): Promise<ApiResponse> => {
    if (!config) {
      return Promise.reject(new Error('配置参数不能为空'));
    }
    return api.post('/ai/test', config)
  },

  // 新的AI配置管理接口
  // 获取所有AI配置
  getAllAIConfigs: (): Promise<ApiResponse<AIModelConfig[]>> => {
    return api.get('/ai/configs')
  },

  // 创建AI配置
  createAIConfig: (config: Omit<AIModelConfig, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<{ config_id: number }>> => {
    return api.post('/ai/configs', config)
  },

  // 更新AI配置
  updateAIConfigById: (id: number, config: Partial<AIModelConfig>): Promise<ApiResponse> => {
    return api.put(`/ai/configs/${id}`, config)
  },

  // 删除AI配置
  deleteAIConfig: (id: number): Promise<ApiResponse> => {
    return api.delete(`/ai/configs/${id}`)
  },

  // 设置当前AI配置
  setCurrentAIConfig: (id: number): Promise<ApiResponse> => {
    return api.post(`/ai/configs/${id}/set-current`)
  },

  // 获取当前AI配置
  getCurrentAIConfig: (): Promise<ApiResponse<AIModelConfig>> => {
    return api.get('/ai/configs/current')
  },

  // 获取配置信息
  getConfig: (): Promise<ApiResponse<any>> => {
    return api.get('/config')
  },

  // 更新配置信息
  updateConfig: (config: any): Promise<ApiResponse> => {
    return api.post('/config', config)
  },

  // 获取历史笔记列表
  getNotesHistory: (): Promise<ApiResponse<HistoryNote[]>> => {
    return api.get('/notes/history')
  },

  // 获取笔记内容
  getNoteContent: (filename: string): Promise<ApiResponse<NoteContentResponse>> => {
    return api.get(`/notes/${encodeURIComponent(filename)}`)
  },

  // 获取提示词文件列表
  getPrompts: (): Promise<ApiResponse<PromptFile[]>> => {
    return api.get('/prompts')
  },

  // 获取字幕文件列表
  getSubtitles: (): Promise<ApiResponse<SubtitleFile[]>> => {
    return api.get('/subtitles')
  },

  // 获取字幕文件内容
  getSubtitleContent: (filename: string): Promise<ApiResponse<SubtitleContentResponse>> => {
    return api.get(`/subtitles/${encodeURIComponent(filename)}`)
  }
}

export default api