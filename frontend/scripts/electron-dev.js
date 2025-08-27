import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import http from 'http'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 等待Vite开发服务器启动
const waitForVite = async () => {
  console.log('等待Vite开发服务器启动...')
  const maxAttempts = 30
  let attempts = 0
  
  while (attempts < maxAttempts) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get('http://localhost:5173', (res) => {
          resolve(res)
        })
        req.on('error', reject)
        req.setTimeout(1000, () => {
          req.destroy()
          reject(new Error('Timeout'))
        })
      })
      console.log('Vite开发服务器已启动')
      return
    } catch (error) {
      attempts++
      if (attempts >= maxAttempts) {
        console.error('等待Vite服务器超时')
        process.exit(1)
      }
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }
}

// 启动Electron
const startElectron = () => {
  console.log('启动Electron应用...')
  const electronPath = path.join(__dirname, '..', 'node_modules', '.bin', 'electron')
  const electronProcess = spawn(electronPath, ['.'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    env: {
      ...process.env,
      NODE_ENV: 'development'
    },
    shell: true
  })
  
  electronProcess.on('close', (code) => {
    console.log(`Electron进程退出，代码: ${code}`)
    process.exit(code)
  })
  
  electronProcess.on('error', (error) => {
    console.error('启动Electron失败:', error)
    process.exit(1)
  })
}

// 主函数
const main = async () => {
  try {
    await waitForVite()
    startElectron()
  } catch (error) {
    console.error('启动失败:', error)
    process.exit(1)
  }
}

main()