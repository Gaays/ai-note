// Electron API 类型定义

interface ElectronAPI {
  // 应用信息
  getAppVersion(): Promise<string>
  getAppPath(name: string): Promise<string>
  getResourcePath(): Promise<string>
  getAppConfig(): Promise<any>
  getSupportedFormats(): Promise<{
    video: string[]
    audio: string[]
    subtitle: string[]
    output: string[]
  }>
  getDefaultPaths(): Promise<{
    output: string
    subtitles: string
    prompts: string
    testVideo?: string
  }>
  getAppInfo(): Promise<{
    name: string
    version: string
    description: string
    author: string
    homepage: string
    platform: string
    arch: string
    electronVersion: string
    nodeVersion: string
  }>

  // 对话框
  showMessageBox(options: any): Promise<any>
  showOpenDialog(options: any): Promise<any>
  showSaveDialog(options: any): Promise<any>

  // 文件系统操作
  readFile(filePath: string): Promise<{ success: boolean; content?: string; error?: string }>
  writeFile(filePath: string, content: string): Promise<{ success: boolean; error?: string }>
  checkFileExists(filePath: string): Promise<boolean>
  createDirectory(dirPath: string): Promise<{ success: boolean; error?: string }>

  // 后端服务管理
  startBackend(): Promise<{ success: boolean; port?: number; error?: string }>
  stopBackend(): Promise<{ success: boolean; error?: string }>
  getBackendStatus(): Promise<{ running: boolean; port: number }>

  // 外部链接
  openExternal(url: string): Promise<{ success: boolean; error?: string }>

  // 窗口控制
  minimizeWindow(): Promise<void>
  toggleMaximizeWindow(): Promise<void>
  closeWindow(): Promise<void>
  restartApp(): Promise<void>

  // 文件选择器（预设配置）
  selectVideoFile(): Promise<{ canceled: boolean; filePaths: string[] }>
  selectOutputFolder(): Promise<{ canceled: boolean; filePaths: string[] }>
  saveNoteFile(defaultPath?: string): Promise<{ canceled: boolean; filePath?: string }>
  selectSubtitleFile(): Promise<{ canceled: boolean; filePaths: string[] }>
  selectConfigFile(): Promise<{ canceled: boolean; filePaths: string[] }>
}

interface Platform {
  isWindows: boolean
  isMac: boolean
  isLinux: boolean
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
    platform: Platform
  }
}

export {}