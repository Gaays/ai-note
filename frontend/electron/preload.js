import { contextBridge, ipcRenderer } from 'electron'

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getAppPath: (name) => ipcRenderer.invoke('get-app-path', name),
  getResourcePath: () => ipcRenderer.invoke('get-resource-path'),
  getAppConfig: () => ipcRenderer.invoke('get-app-config'),
  getSupportedFormats: () => ipcRenderer.invoke('get-supported-formats'),
  getDefaultPaths: () => ipcRenderer.invoke('get-default-paths'),
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  
  // 对话框
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // 文件系统操作
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  checkFileExists: (filePath) => ipcRenderer.invoke('check-file-exists', filePath),
  createDirectory: (dirPath) => ipcRenderer.invoke('create-directory', dirPath),
  
  // 后端服务管理
  startBackend: () => ipcRenderer.invoke('start-backend'),
  stopBackend: () => ipcRenderer.invoke('stop-backend'),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  
  // 外部链接
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // 窗口控制
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  toggleMaximizeWindow: () => ipcRenderer.invoke('toggle-maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  restartApp: () => ipcRenderer.invoke('restart-app'),
  
  // 文件选择器（预设配置）
  selectVideoFile: () => ipcRenderer.invoke('show-open-dialog', {
    title: '选择音视频文件',
    filters: [
      {
        name: '音视频文件',
        extensions: ['mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'flac', 'm4a', 'webm', 'ogg']
      },
      { name: '所有文件', extensions: ['*'] }
    ],
    properties: ['openFile']
  }),
  
  selectOutputFolder: () => ipcRenderer.invoke('show-open-dialog', {
    title: '选择输出文件夹',
    properties: ['openDirectory']
  }),
  
  saveNoteFile: (defaultPath) => ipcRenderer.invoke('show-save-dialog', {
    title: '保存笔记文件',
    defaultPath: defaultPath,
    filters: [
      { name: 'Markdown文件', extensions: ['md'] },
      { name: '文本文件', extensions: ['txt'] },
      { name: '所有文件', extensions: ['*'] }
    ]
  }),
  
  selectSubtitleFile: () => ipcRenderer.invoke('show-open-dialog', {
    title: '选择字幕文件',
    filters: [
      {
        name: '字幕文件',
        extensions: ['srt', 'vtt', 'ass', 'ssa']
      },
      { name: '所有文件', extensions: ['*'] }
    ],
    properties: ['openFile']
  }),
  
  selectConfigFile: () => ipcRenderer.invoke('show-open-dialog', {
    title: '选择配置文件',
    filters: [
      { name: 'JSON文件', extensions: ['json'] },
      { name: '所有文件', extensions: ['*'] }
    ],
    properties: ['openFile']
  })
})

// 平台信息
contextBridge.exposeInMainWorld('platform', {
  isWindows: process.platform === 'win32',
  isMac: process.platform === 'darwin',
  isLinux: process.platform === 'linux'
})