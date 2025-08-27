import { ref, onMounted } from 'vue'

// Electron API 组合式函数
export function useElectron() {
  const isElectron = ref(false)
  const appInfo = ref<any>(null)
  const backendStatus = ref({ running: false, port: 5000 })
  const supportedFormats = ref<any>(null)
  const defaultPaths = ref<any>(null)

  // 检查是否在Electron环境中
  const checkElectronEnvironment = () => {
    isElectron.value = !!(window && window.electronAPI)
    return isElectron.value
  }

  // 获取应用信息
  const getAppInfo = async () => {
    if (!isElectron.value) return null
    try {
      appInfo.value = await window.electronAPI.getAppInfo()
      return appInfo.value
    } catch (error) {
      console.error('获取应用信息失败:', error)
      return null
    }
  }

  // 获取后端状态
  const getBackendStatus = async () => {
    if (!isElectron.value) return backendStatus.value
    try {
      backendStatus.value = await window.electronAPI.getBackendStatus()
      return backendStatus.value
    } catch (error) {
      console.error('获取后端状态失败:', error)
      return backendStatus.value
    }
  }

  // 启动后端服务
  const startBackend = async () => {
    if (!isElectron.value) return { success: false, error: '不在Electron环境中' }
    try {
      const result = await window.electronAPI.startBackend()
      if (result.success) {
        await getBackendStatus()
      }
      return result
    } catch (error) {
      console.error('启动后端服务失败:', error)
      return { success: false, error: error.message }
    }
  }

  // 停止后端服务
  const stopBackend = async () => {
    if (!isElectron.value) return { success: false, error: '不在Electron环境中' }
    try {
      const result = await window.electronAPI.stopBackend()
      if (result.success) {
        await getBackendStatus()
      }
      return result
    } catch (error) {
      console.error('停止后端服务失败:', error)
      return { success: false, error: error.message }
    }
  }

  // 获取支持的文件格式
  const getSupportedFormats = async () => {
    if (!isElectron.value) return null
    try {
      supportedFormats.value = await window.electronAPI.getSupportedFormats()
      return supportedFormats.value
    } catch (error) {
      console.error('获取支持的文件格式失败:', error)
      return null
    }
  }

  // 获取默认路径
  const getDefaultPaths = async () => {
    if (!isElectron.value) return null
    try {
      defaultPaths.value = await window.electronAPI.getDefaultPaths()
      return defaultPaths.value
    } catch (error) {
      console.error('获取默认路径失败:', error)
      return null
    }
  }

  // 文件操作
  const fileOperations = {
    // 选择视频文件
    selectVideoFile: async () => {
      if (!isElectron.value) return { canceled: true, filePaths: [] }
      try {
        return await window.electronAPI.selectVideoFile()
      } catch (error) {
        console.error('选择视频文件失败:', error)
        return { canceled: true, filePaths: [] }
      }
    },

    // 选择输出文件夹
    selectOutputFolder: async () => {
      if (!isElectron.value) return { canceled: true, filePaths: [] }
      try {
        return await window.electronAPI.selectOutputFolder()
      } catch (error) {
        console.error('选择输出文件夹失败:', error)
        return { canceled: true, filePaths: [] }
      }
    },

    // 保存笔记文件
    saveNoteFile: async (defaultPath?: string) => {
      if (!isElectron.value) return { canceled: true }
      try {
        return await window.electronAPI.saveNoteFile(defaultPath)
      } catch (error) {
        console.error('保存笔记文件失败:', error)
        return { canceled: true }
      }
    },

    // 选择字幕文件
    selectSubtitleFile: async () => {
      if (!isElectron.value) return { canceled: true, filePaths: [] }
      try {
        return await window.electronAPI.selectSubtitleFile()
      } catch (error) {
        console.error('选择字幕文件失败:', error)
        return { canceled: true, filePaths: [] }
      }
    },

    // 读取文件
    readFile: async (filePath: string) => {
      if (!isElectron.value) return { success: false, error: '不在Electron环境中' }
      try {
        return await window.electronAPI.readFile(filePath)
      } catch (error) {
        console.error('读取文件失败:', error)
        return { success: false, error: error.message }
      }
    },

    // 写入文件
    writeFile: async (filePath: string, content: string) => {
      if (!isElectron.value) return { success: false, error: '不在Electron环境中' }
      try {
        return await window.electronAPI.writeFile(filePath, content)
      } catch (error) {
        console.error('写入文件失败:', error)
        return { success: false, error: error.message }
      }
    },

    // 检查文件是否存在
    checkFileExists: async (filePath: string) => {
      if (!isElectron.value) return false
      try {
        return await window.electronAPI.checkFileExists(filePath)
      } catch (error) {
        console.error('检查文件存在失败:', error)
        return false
      }
    },

    // 创建目录
    createDirectory: async (dirPath: string) => {
      if (!isElectron.value) return { success: false, error: '不在Electron环境中' }
      try {
        return await window.electronAPI.createDirectory(dirPath)
      } catch (error) {
        console.error('创建目录失败:', error)
        return { success: false, error: error.message }
      }
    }
  }

  // 窗口操作
  const windowOperations = {
    minimize: async () => {
      if (!isElectron.value) return
      try {
        await window.electronAPI.minimizeWindow()
      } catch (error) {
        console.error('最小化窗口失败:', error)
      }
    },

    toggleMaximize: async () => {
      if (!isElectron.value) return
      try {
        await window.electronAPI.toggleMaximizeWindow()
      } catch (error) {
        console.error('切换最大化窗口失败:', error)
      }
    },

    close: async () => {
      if (!isElectron.value) return
      try {
        await window.electronAPI.closeWindow()
      } catch (error) {
        console.error('关闭窗口失败:', error)
      }
    },

    restart: async () => {
      if (!isElectron.value) return
      try {
        await window.electronAPI.restartApp()
      } catch (error) {
        console.error('重启应用失败:', error)
      }
    }
  }

  // 其他操作
  const openExternal = async (url: string) => {
    if (!isElectron.value) {
      window.open(url, '_blank')
      return { success: true }
    }
    try {
      return await window.electronAPI.openExternal(url)
    } catch (error) {
      console.error('打开外部链接失败:', error)
      return { success: false, error: error.message }
    }
  }

  // 显示消息框
  const showMessageBox = async (options: any) => {
    if (!isElectron.value) {
      alert(options.message || '消息')
      return { response: 0 }
    }
    try {
      return await window.electronAPI.showMessageBox(options)
    } catch (error) {
      console.error('显示消息框失败:', error)
      return { response: 0 }
    }
  }

  // 初始化
  onMounted(async () => {
    if (checkElectronEnvironment()) {
      await Promise.all([
        getAppInfo(),
        getBackendStatus(),
        getSupportedFormats(),
        getDefaultPaths()
      ])
    }
  })

  return {
    // 状态
    isElectron,
    appInfo,
    backendStatus,
    supportedFormats,
    defaultPaths,

    // 方法
    checkElectronEnvironment,
    getAppInfo,
    getBackendStatus,
    startBackend,
    stopBackend,
    getSupportedFormats,
    getDefaultPaths,
    fileOperations,
    windowOperations,
    openExternal,
    showMessageBox
  }
}

// 平台检测组合式函数
export function usePlatform() {
  const platform = ref({
    isWindows: false,
    isMac: false,
    isLinux: false
  })

  onMounted(() => {
    if (window && window.platform) {
      platform.value = window.platform
    } else {
      // 浏览器环境下的平台检测
      const userAgent = navigator.userAgent.toLowerCase()
      platform.value = {
        isWindows: userAgent.includes('win'),
        isMac: userAgent.includes('mac'),
        isLinux: userAgent.includes('linux')
      }
    }
  })

  return {
    platform
  }
}