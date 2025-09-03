const { contextBridge, ipcRenderer } = require('electron')

// 暴露给渲染进程的API
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 对话框
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // 文件系统
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  fileExists: (filePath) => ipcRenderer.invoke('file-exists', filePath),
  createDirectory: (dirPath) => ipcRenderer.invoke('create-directory', dirPath),
  
  // 后端服务
  startBackendService: () => ipcRenderer.invoke('start-backend-service'),
  stopBackendService: () => ipcRenderer.invoke('stop-backend-service'),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  
  // 外部链接
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // 窗口控制
  restartApp: () => ipcRenderer.invoke('restart-app'),
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  unmaximizeWindow: () => ipcRenderer.invoke('unmaximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  
  // 路径相关
  getPath: (name) => ipcRenderer.invoke('get-path', name),
  
  // 应用配置
  getAppConfig: () => ipcRenderer.invoke('get-app-config'),
  
  // 支持的格式
  getSupportedFormats: () => ipcRenderer.invoke('get-supported-formats'),
  
  // 默认路径
  getDefaultPaths: () => ipcRenderer.invoke('get-default-paths'),
  
  // 应用信息
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  
  // 文件选择
  selectVideoFile: () => ipcRenderer.invoke('select-video-file'),
  selectSubtitleFile: () => ipcRenderer.invoke('select-subtitle-file'),
  selectExportPath: () => ipcRenderer.invoke('select-export-path'),
  
  // 日志功能
  logger: {
    info: (message, ...args) => ipcRenderer.invoke('log-info', message, ...args),
    warn: (message, ...args) => ipcRenderer.invoke('log-warn', message, ...args),
    error: (message, ...args) => ipcRenderer.invoke('log-error', message, ...args),
    debug: (message, ...args) => ipcRenderer.invoke('log-debug', message, ...args),
    getLogDirectory: () => ipcRenderer.invoke('get-log-directory'),
    getLogFiles: () => ipcRenderer.invoke('get-log-files')
  }
})

// 暴露平台信息
contextBridge.exposeInMainWorld('platform', {
  isWindows: process.platform === 'win32',
  isMac: process.platform === 'darwin',
  isLinux: process.platform === 'linux'
})

console.log('Preload script loaded successfully')