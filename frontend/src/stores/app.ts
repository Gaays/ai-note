import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { WhisperModel, AIModelConfig } from '../services/api'

// 本地存储键名
const AI_CONFIG_KEY = 'ai_config'
const WHISPER_MODEL_KEY = 'current_whisper_model'

// 从本地存储加载配置
const loadAIConfigFromStorage = (): AIModelConfig => {
  try {
    const stored = localStorage.getItem(AI_CONFIG_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('加载AI配置失败:', error)
  }
  return {
    provider: 'openai',
    api_key: '',
    model_name: 'gpt-3.5-turbo',
    base_url: ''
  }
}

const loadWhisperModelFromStorage = (): string => {
  try {
    return localStorage.getItem(WHISPER_MODEL_KEY) || ''
  } catch (error) {
    console.error('加载Whisper模型配置失败:', error)
    return ''
  }
}

export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const currentFile = ref<File | null>(null)
  const currentFileId = ref<string>('')
  const subtitleText = ref<string>('')
  const noteContent = ref<string>('')
  const whisperModels = ref<WhisperModel[]>([])
  const currentWhisperModel = ref<string>('')
  const aiConfig = ref<AIModelConfig>(loadAIConfigFromStorage())
  const config = ref<any>({})
  
  // 初始化时从本地存储加载Whisper模型
  const storedWhisperModel = loadWhisperModelFromStorage()
  if (storedWhisperModel) {
    currentWhisperModel.value = storedWhisperModel
  }
  
  // 监听AI配置变化，自动保存到本地存储
  watch(aiConfig, (newConfig) => {
    try {
      localStorage.setItem(AI_CONFIG_KEY, JSON.stringify(newConfig))
    } catch (error) {
      console.error('保存AI配置到本地存储失败:', error)
    }
  }, { deep: true })
  
  // 监听Whisper模型变化，自动保存到本地存储
  watch(currentWhisperModel, (newModel) => {
    try {
      if (newModel) {
        localStorage.setItem(WHISPER_MODEL_KEY, newModel)
      }
    } catch (error) {
      console.error('保存Whisper模型配置到本地存储失败:', error)
    }
  })

  // 计算属性
  const hasFile = computed(() => !!currentFile.value)
  const hasSubtitle = computed(() => !!subtitleText.value)
  const hasNote = computed(() => !!noteContent.value)
  const isAIConfigured = computed(() => !!aiConfig.value.api_key)

  // 方法
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const setCurrentFile = (file: File | null) => {
    currentFile.value = file
    if (!file) {
      currentFileId.value = ''
      subtitleText.value = ''
      noteContent.value = ''
    }
  }

  const setCurrentFileId = (fileId: string) => {
    currentFileId.value = fileId
  }

  const setSubtitleText = (text: string) => {
    subtitleText.value = text
  }

  const setNoteContent = (content: string) => {
    noteContent.value = content
  }

  const setWhisperModels = (models: WhisperModel[]) => {
    whisperModels.value = models
    // 设置当前模型
    const current = models.find(m => m.is_current)
    if (current) {
      currentWhisperModel.value = current.name
    }
  }

  const setCurrentWhisperModel = (modelName: string) => {
    currentWhisperModel.value = modelName
    // 更新模型列表中的当前状态
    whisperModels.value.forEach(model => {
      model.is_current = model.name === modelName
    })
  }

  const setAIConfig = (newConfig: AIModelConfig) => {
    aiConfig.value = { ...newConfig }
    // 手动触发保存到本地存储
    try {
      localStorage.setItem(AI_CONFIG_KEY, JSON.stringify(newConfig))
    } catch (error) {
      console.error('保存AI配置到本地存储失败:', error)
    }
  }

  const setConfig = (newConfig: any) => {
    config.value = { ...newConfig }
  }

  const clearAll = () => {
    currentFile.value = null
    currentFileId.value = ''
    subtitleText.value = ''
    noteContent.value = ''
    loading.value = false
  }

  return {
    // 状态
    loading,
    currentFile,
    currentFileId,
    subtitleText,
    noteContent,
    whisperModels,
    currentWhisperModel,
    aiConfig,
    config,
    
    // 计算属性
    hasFile,
    hasSubtitle,
    hasNote,
    isAIConfigured,
    
    // 方法
    setLoading,
    setCurrentFile,
    setCurrentFileId,
    setSubtitleText,
    setNoteContent,
    setWhisperModels,
    setCurrentWhisperModel,
    setAIConfig,
    setConfig,
    clearAll
  }
})