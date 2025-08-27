const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn } = require('child_process')

const isDev = process.env.NODE_ENV === 'development'

// 简化的配置对象
const config = {
  current: {
    backend: {
      port: 5000,
      path: path.join(__dirname, '..', '..', 'backend')
    },
    frontend: {
      url: isDev ? 'http://localhost:5173' : null,
      file: isDev ? null : '../dist/index.html'
    },
    window: {
      width: 1200,
      height: 800,
      devTools: isDev
    }
  }
}

// 后端服务进程
let backendProcess = null
let backendPort = config.current.backend.port

function createWindow() {
  const windowConfig = config.current.window
  
  const mainWindow = new BrowserWindow({
    width: windowConfig.width,
    height: windowConfig.height,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/favicon.ico'),
    show: false,
    titleBarStyle: 'default',
    minWidth: 800,
    minHeight: 600
  })

  // 加载应用
  if (isDev) {
    mainWindow.loadURL(config.current.frontend.url)
    if (windowConfig.devTools) {
      mainWindow.webContents.openDevTools()
    }
  } else {
    mainWindow.loadFile(config.current.frontend.file)
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    // 自动启动后端服务
    startBackendService()
  })

  mainWindow.on('closed', () => {
    app.quit()
  })
  
  return mainWindow
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// 启动后端服务
function startBackendService() {
  if (backendProcess) {
    console.log('Backend service is already running')
    return Promise.resolve()
  }
  
  return new Promise((resolve, reject) => {
    const backendPath = config.current.backend.path
    const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3'
    
    // 检查后端目录是否存在
    if (!fs.existsSync(backendPath)) {
      const error = `Backend directory not found: ${backendPath}`
      console.error(error)
      reject(new Error(error))
      return
    }
    
    console.log(`Starting backend service from: ${backendPath}`)
    
    backendProcess = spawn(pythonExecutable, ['app.py'], {
      cwd: backendPath,
      env: { 
        ...process.env, 
        PORT: backendPort.toString(),
        PYTHONPATH: backendPath
      },
      stdio: ['pipe', 'pipe', 'pipe']
    })
    
    let startupTimeout = setTimeout(() => {
      console.log('Backend startup timeout, assuming success')
      resolve()
    }, 10000) // 10秒超时
    
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString()
      console.log(`Backend stdout: ${output}`)
      
      // 检查服务是否启动成功
      if (output.includes('Running on') || output.includes('started')) {
        clearTimeout(startupTimeout)
        resolve()
      }
    })
    
    backendProcess.stderr.on('data', (data) => {
      const error = data.toString()
      console.error(`Backend stderr: ${error}`)
      
      // 如果是严重错误，拒绝Promise
      if (error.includes('Error') || error.includes('Exception')) {
        clearTimeout(startupTimeout)
        reject(new Error(error))
      }
    })
    
    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`)
      backendProcess = null
      clearTimeout(startupTimeout)
      
      if (code !== 0) {
        reject(new Error(`Backend process exited with code ${code}`))
      }
    })
    
    backendProcess.on('error', (error) => {
      console.error('Failed to start backend process:', error)
      clearTimeout(startupTimeout)
      reject(error)
    })
  })
}

// 停止后端服务
function stopBackendService() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

// 应用退出时清理
app.on('before-quit', () => {
  stopBackendService()
})

// IPC 处理器
ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

ipcMain.handle('show-message-box', async (event, options) => {
  return await dialog.showMessageBox(options)
})

ipcMain.handle('show-open-dialog', async (event, options) => {
  return await dialog.showOpenDialog(options)
})

ipcMain.handle('show-save-dialog', async (event, options) => {
  return await dialog.showSaveDialog(options)
})

// 文件系统操作
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8')
    return { success: true, content }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('write-file', async (event, filePath, content) => {
  try {
    await fs.promises.writeFile(filePath, content, 'utf-8')
    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('check-file-exists', async (event, filePath) => {
  try {
    await fs.promises.access(filePath)
    return true
  } catch {
    return false
  }
})

ipcMain.handle('create-directory', async (event, dirPath) => {
  try {
    await fs.promises.mkdir(dirPath, { recursive: true })
    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

// 后端服务管理
ipcMain.handle('start-backend', async () => {
  try {
    startBackendService()
    return { success: true, port: backendPort }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('stop-backend', async () => {
  try {
    stopBackendService()
    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('get-backend-status', () => {
  return {
    running: backendProcess !== null,
    port: backendPort
  }
})

// 打开外部链接
ipcMain.handle('open-external', async (event, url) => {
  try {
    await shell.openExternal(url)
    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

// 获取应用路径
ipcMain.handle('get-app-path', (event, name) => {
  return app.getPath(name)
})

// 获取资源路径
ipcMain.handle('get-resource-path', () => {
  return isDev ? path.join(__dirname, '../..') : process.resourcesPath
})

// 获取应用配置
ipcMain.handle('get-app-config', () => {
  return config
})

// 获取支持的文件格式
ipcMain.handle('get-supported-formats', () => {
  return config.supportedFormats
})

// 获取默认路径
ipcMain.handle('get-default-paths', () => {
  return config.paths
})

// 获取应用信息
ipcMain.handle('get-app-info', () => {
  return {
    ...config.app,
    version: app.getVersion(),
    platform: process.platform,
    arch: process.arch,
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node
  }
})

// 重启应用
ipcMain.handle('restart-app', () => {
  app.relaunch()
  app.exit()
})

// 最小化窗口
ipcMain.handle('minimize-window', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    focusedWindow.minimize()
  }
})

// 最大化/还原窗口
ipcMain.handle('toggle-maximize-window', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    if (focusedWindow.isMaximized()) {
      focusedWindow.unmaximize()
    } else {
      focusedWindow.maximize()
    }
  }
})

// 关闭窗口
ipcMain.handle('close-window', () => {
  const focusedWindow = BrowserWindow.getFocusedWindow()
  if (focusedWindow) {
    focusedWindow.close()
  }
})