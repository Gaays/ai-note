const { contextBridge, ipcRenderer } = require('electron')

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 应用信息
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 对话框
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // 文件操作
  selectVideoFile: () => ipcRenderer.invoke('show-open-dialog', {
    title: '选择音视频文件',
    filters: [
      {
        name: '音视频文件',
        extensions: ['mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'flac', 'm4a']
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
  })
})

// 平台信息
contextBridge.exposeInMainWorld('platform', {
  isWindows: process.platform === 'win32',
  isMac: process.platform === 'darwin',
  isLinux: process.platform === 'linux'
})