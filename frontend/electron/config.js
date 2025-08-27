import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const isDev = process.env.NODE_ENV === 'development'

const config = {
  // 开发环境配置
  development: {
    backend: {
      host: 'localhost',
      port: 5000,
      path: path.join(__dirname, '../../backend')
    },
    frontend: {
      url: 'http://localhost:5173'
    },
    window: {
      width: 1200,
      height: 800,
      devTools: true
    }
  },
  
  // 生产环境配置
  production: {
    backend: {
      host: 'localhost',
      port: 5000,
      path: path.join(process.resourcesPath, 'backend')
    },
    frontend: {
      file: path.join(__dirname, '../dist/index.html')
    },
    window: {
      width: 1200,
      height: 800,
      devTools: false
    }
  },
  
  // 获取当前环境配置
  get current() {
    return isDev ? this.development : this.production
  },
  
  // 应用配置
  app: {
    name: 'AI Note Generator',
    version: '1.0.0',
    description: 'AI-powered video note generator with subtitle extraction',
    author: 'Gaays',
    homepage: 'https://github.com/Gaays/ai-note'
  },
  
  // 文件路径配置
  paths: {
    output: isDev ? path.join(__dirname, '../../Output') : path.join(process.cwd(), 'Output'),
    subtitles: isDev ? path.join(__dirname, '../../Subtitles') : path.join(process.cwd(), 'Subtitles'),
    prompts: isDev ? path.join(__dirname, '../../Prompts') : path.join(process.cwd(), 'Prompts'),
    testVideo: isDev ? path.join(__dirname, '../../test-video') : null
  },
  
  // 支持的文件格式
  supportedFormats: {
    video: ['mp4', 'avi', 'mov', 'mkv', 'webm'],
    audio: ['mp3', 'wav', 'flac', 'm4a', 'ogg'],
    subtitle: ['srt', 'vtt', 'ass', 'ssa'],
    output: ['md', 'txt']
  },
  
  // 默认设置
  defaults: {
    language: 'zh',
    outputFormat: 'md',
    promptType: '详细',
    whisperModel: 'base',
    aiProvider: 'openai'
  }
}

export default config