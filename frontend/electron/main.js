import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron'
import path from 'path'
import fs from 'fs'
import { spawn } from 'child_process'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import logger from './logger.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const isDev = process.env.NODE_ENV === 'development'

// 初始化日志系统
logger.init()

// 全局错误处理
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', error)
  console.error('Uncaught Exception:', error)
})

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', { reason, promise: promise.toString() })
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
})

// Electron 错误处理
app.on('render-process-gone', (event, webContents, details) => {
  logger.error('Render process gone', { reason: details.reason, exitCode: details.exitCode })
})

app.on('child-process-gone', (event, details) => {
  logger.error('Child process gone', { type: details.type, reason: details.reason, exitCode: details.exitCode })
})

// 简化的配置对象
const config = {
  current: {
    backend: {
      port: 5000,
      path: isDev ? path.join(__dirname, '..', '..', 'backend') : path.join(process.resourcesPath, 'backend', 'video-note-backend'),
      executable: isDev ? null : (process.platform === 'win32' ? 'video-note-backend.exe' : 'video-note-backend')
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
  try {
    logger.info('Creating main window')
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

    // 监听窗口错误
    mainWindow.webContents.on('crashed', (event) => {
      logger.error('Window crashed', event)
    })

    mainWindow.webContents.on('unresponsive', () => {
      logger.warn('Window became unresponsive')
    })

    mainWindow.webContents.on('responsive', () => {
      logger.info('Window became responsive again')
    })

    // 加载应用
    if (isDev) {
      logger.info('Loading development URL:', config.current.frontend.url)
      mainWindow.loadURL(config.current.frontend.url)
      if (windowConfig.devTools) {
        mainWindow.webContents.openDevTools()
      }
    } else {
      logger.info('Loading production file:', config.current.frontend.file)
      mainWindow.loadFile(config.current.frontend.file)
    }

    mainWindow.once('ready-to-show', () => {
      logger.info('Main window ready to show')
      mainWindow.show()
      // 自动启动后端服务
      startBackendService()
    })

    mainWindow.on('closed', () => {
      logger.info('Main window closed')
      app.quit()
    })

    logger.info('Main window created successfully')
    return mainWindow
  } catch (error) {
    logger.error('Failed to create main window', error)
    throw error
  }
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
    logger.info('Backend service is already running')
    return Promise.resolve()
  }

  return new Promise((resolve, reject) => {
    try {
      logger.info('Starting backend service')
      const backendPath = config.current.backend.path
      const backendExecutable = config.current.backend.executable

      // 检查后端目录是否存在
      if (!fs.existsSync(backendPath)) {
        const error = `Backend directory not found: ${backendPath}`
        logger.error(error)
        reject(new Error(error))
        return
      }

      logger.info(`Starting backend service from: ${backendPath}`)

    let command, args, cwd

    if (isDev) {
      // 开发模式：使用Python直接运行
      const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3'
      command = pythonExecutable
      args = ['app.py']
      cwd = backendPath
    } else {
      // 生产模式：使用打包后的可执行文件
      const executablePath = path.join(backendPath, backendExecutable)
      if (!fs.existsSync(executablePath)) {
        const error = `Backend executable not found: ${executablePath}`
        console.error(error)
        reject(new Error(error))
        return
      }
      command = executablePath
      args = []
      cwd = backendPath
    }

      logger.info(`Spawning backend process: ${command} ${args.join(' ')}`)
      backendProcess = spawn(command, args, {
        cwd: cwd,
        env: {
          ...process.env,
          PORT: backendPort.toString(),
          PYTHONPATH: isDev ? backendPath : undefined
        },
        stdio: ['pipe', 'pipe', 'pipe']
      })

      let startupTimeout = setTimeout(() => {
        logger.warn('Backend startup timeout, assuming success')
        resolve()
      }, 10000) // 10秒超时

      backendProcess.stdout.on('data', (data) => {
        const output = data.toString()
        logger.debug(`Backend stdout: ${output.trim()}`)

        // 检查服务是否启动成功
        if (output.includes('Running on') || output.includes('started')) {
          logger.info('Backend service started successfully')
          clearTimeout(startupTimeout)
          resolve()
        }
      })

      backendProcess.stderr.on('data', (data) => {
        const error = data.toString()
        logger.error(`Backend stderr: ${error.trim()}`)

        // 如果是严重错误，拒绝Promise
        if (error.includes('Error') || error.includes('Exception')) {
          clearTimeout(startupTimeout)
          reject(new Error(error))
        }
      })

      backendProcess.on('close', (code) => {
        logger.info(`Backend process exited with code ${code}`)
        backendProcess = null
        clearTimeout(startupTimeout)

        if (code !== 0) {
          const error = `Backend process exited with code ${code}`
          logger.error(error)
          reject(new Error(error))
        }
      })

      backendProcess.on('error', (error) => {
        logger.error('Failed to start backend process', error)
        clearTimeout(startupTimeout)
        reject(error)
      })
    } catch (error) {
      logger.error('Error in startBackendService', error)
      reject(error)
    }
  })
}

// 停止后端服务
function stopBackendService() {
  if (backendProcess) {
    logger.info('Stopping backend service')
    backendProcess.kill()
    backendProcess = null
    logger.info('Backend service stopped')
  }
}

// 应用退出时清理
app.on('before-quit', () => {
  logger.info('Application is quitting')
  stopBackendService()
})

app.on('will-quit', () => {
  logger.info('Application will quit')
})

app.on('quit', () => {
  logger.info('Application quit')
})

// IPC 处理器
ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

// 日志相关的IPC处理器
ipcMain.handle('log-info', (event, message, ...args) => {
  logger.info(message, ...args)
})

ipcMain.handle('log-warn', (event, message, ...args) => {
  logger.warn(message, ...args)
})

ipcMain.handle('log-error', (event, message, ...args) => {
  logger.error(message, ...args)
})

ipcMain.handle('log-debug', (event, message, ...args) => {
  logger.debug(message, ...args)
})

// 获取日志目录
ipcMain.handle('get-log-directory', () => {
  return logger.getLogDirectory()
})

// 获取日志文件列表
ipcMain.handle('get-log-files', () => {
  return logger.getLogFiles()
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