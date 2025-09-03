import fs from 'fs'
import path from 'path'
import { app } from 'electron'

class Logger {
  constructor() {
    this.logDir = null
    this.logFile = null
    this.maxLogSize = 10 * 1024 * 1024 // 10MB
    this.maxLogFiles = 5
    this.initialized = false
  }

  // 初始化日志系统
  init() {
    try {
      // 获取用户数据目录
      const userDataPath = app.getPath('userData')
      this.logDir = path.join(userDataPath, 'logs')
      
      // 创建日志目录
      if (!fs.existsSync(this.logDir)) {
        fs.mkdirSync(this.logDir, { recursive: true })
      }
      
      // 设置日志文件路径
      const timestamp = new Date().toISOString().split('T')[0]
      this.logFile = path.join(this.logDir, `app-${timestamp}.log`)
      
      this.initialized = true
      this.info('Logger initialized successfully')
      
      // 清理旧日志文件
      this.cleanOldLogs()
      
    } catch (error) {
      console.error('Failed to initialize logger:', error)
    }
  }

  // 写入日志
  writeLog(level, message, error = null) {
    if (!this.initialized) {
      console.log(`[${level}] ${message}`, error || '')
      return
    }

    try {
      const timestamp = new Date().toISOString()
      let logEntry = `[${timestamp}] [${level.toUpperCase()}] ${message}`
      
      if (error) {
        if (error instanceof Error) {
          logEntry += `\nError: ${error.message}\nStack: ${error.stack}`
        } else {
          logEntry += `\nError: ${JSON.stringify(error)}`
        }
      }
      
      logEntry += '\n'
      
      // 检查文件大小，如果超过限制则轮转
      this.rotateLogIfNeeded()
      
      // 写入文件
      fs.appendFileSync(this.logFile, logEntry, 'utf8')
      
      // 同时输出到控制台
      console.log(`[${level.toUpperCase()}] ${message}`, error || '')
      
    } catch (writeError) {
      console.error('Failed to write log:', writeError)
    }
  }

  // 日志轮转
  rotateLogIfNeeded() {
    try {
      if (!fs.existsSync(this.logFile)) {
        return
      }
      
      const stats = fs.statSync(this.logFile)
      if (stats.size >= this.maxLogSize) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
        const rotatedFile = path.join(this.logDir, `app-${timestamp}.log`)
        
        // 重命名当前日志文件
        fs.renameSync(this.logFile, rotatedFile)
        
        // 创建新的日志文件
        const newTimestamp = new Date().toISOString().split('T')[0]
        this.logFile = path.join(this.logDir, `app-${newTimestamp}.log`)
        
        this.info('Log file rotated')
      }
    } catch (error) {
      console.error('Failed to rotate log file:', error)
    }
  }

  // 清理旧日志文件
  cleanOldLogs() {
    try {
      const files = fs.readdirSync(this.logDir)
      const logFiles = files
        .filter(file => file.startsWith('app-') && file.endsWith('.log'))
        .map(file => ({
          name: file,
          path: path.join(this.logDir, file),
          mtime: fs.statSync(path.join(this.logDir, file)).mtime
        }))
        .sort((a, b) => b.mtime - a.mtime)
      
      // 保留最新的几个文件，删除其余的
      if (logFiles.length > this.maxLogFiles) {
        const filesToDelete = logFiles.slice(this.maxLogFiles)
        filesToDelete.forEach(file => {
          try {
            fs.unlinkSync(file.path)
            console.log(`Deleted old log file: ${file.name}`)
          } catch (error) {
            console.error(`Failed to delete log file ${file.name}:`, error)
          }
        })
      }
    } catch (error) {
      console.error('Failed to clean old logs:', error)
    }
  }

  // 日志级别方法
  info(message, data = null) {
    this.writeLog('info', message, data)
  }

  warn(message, data = null) {
    this.writeLog('warn', message, data)
  }

  error(message, error = null) {
    this.writeLog('error', message, error)
  }

  debug(message, data = null) {
    this.writeLog('debug', message, data)
  }

  // 获取日志目录
  getLogDir() {
    return this.logDir
  }

  // 获取当前日志文件
  getCurrentLogFile() {
    return this.logFile
  }

  // 获取所有日志文件
  getAllLogFiles() {
    try {
      if (!this.logDir || !fs.existsSync(this.logDir)) {
        return []
      }
      
      const files = fs.readdirSync(this.logDir)
      return files
        .filter(file => file.startsWith('app-') && file.endsWith('.log'))
        .map(file => path.join(this.logDir, file))
        .sort()
    } catch (error) {
      this.error('Failed to get log files', error)
      return []
    }
  }

  // 读取日志文件内容
  readLogFile(filePath, lines = 100) {
    try {
      if (!fs.existsSync(filePath)) {
        return ''
      }
      
      const content = fs.readFileSync(filePath, 'utf8')
      const allLines = content.split('\n')
      
      // 返回最后N行
      const startIndex = Math.max(0, allLines.length - lines)
      return allLines.slice(startIndex).join('\n')
    } catch (error) {
      this.error('Failed to read log file', error)
      return ''
    }
  }
}

// 创建全局日志实例
const logger = new Logger()

export default logger