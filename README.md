# 视频笔记生成器 (Video Note Generator)

一个基于AI的智能视频笔记生成工具，能够自动提取视频/音频文件的字幕并生成结构化的学习笔记。

## 🚀 功能特性

- **多格式支持**: 支持MP4、MP3、WAV、M4A等多种音视频格式
- **智能字幕提取**: 基于Whisper模型的高精度语音识别
- **AI笔记生成**: 支持OpenAI、Anthropic、Google Gemini等多种AI模型
- **自定义提示词**: 内置多种笔记模板，支持自定义提示词
- **历史记录管理**: 完整的笔记历史记录和管理功能
- **现代化界面**: 基于Vue 3和Element Plus的响应式UI
- **实时进度显示**: 文件处理和笔记生成的实时进度反馈
- **跨平台桌面应用**: 支持Windows、macOS、Linux桌面应用
- **原生系统集成**: 文件拖拽、系统通知、菜单栏等原生体验

## 🛠️ 技术栈

### 前端

- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全的JavaScript超集
- **Element Plus** - Vue 3组件库
- **Vite** - 现代化构建工具
- **Pinia** - Vue状态管理
- **Axios** - HTTP客户端

### 后端

- **Python 3.8+** - 后端开发语言
- **Flask** - 轻量级Web框架
- **Faster-Whisper** - 高性能语音识别引擎
- **OpenAI API** - GPT模型接口
- **Anthropic API** - Claude模型接口
- **Google Generative AI** - Gemini模型接口
- **SQLite** - 轻量级数据库

### 桌面应用

- **Electron** - 跨平台桌面应用框架
- **Electron Builder** - 应用打包和分发工具

### 其他工具

- **Git** - 版本控制
- **PNPM** - 高效的包管理器

## 📋 环境要求

### 系统要求

- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **内存**: 建议8GB以上（处理大文件时）
- **存储**: 至少2GB可用空间（用于模型和临时文件）

### 依赖要求

- **FFmpeg**: 音视频处理（自动下载或手动安装）
- **CUDA**: 可选，用于GPU加速（NVIDIA显卡）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-note
```

### 2. 后端设置

#### 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加你的API密钥
# OPENAI_API_KEY=your_openai_api_key
# ANTHROPIC_API_KEY=your_anthropic_api_key
# GOOGLE_API_KEY=your_google_api_key
```

#### 启动后端服务

```bash
python app.py
```

后端服务将在 `http://localhost:5000` 启动

### 3. 前端设置

#### 安装Node.js依赖

```bash
cd frontend
pnpm install
```

#### 启动开发服务器

```bash
pnpm dev
```

前端应用将在 `http://localhost:5173` 启动

### 4. 桌面应用（可选）

#### 开发环境运行

```bash
cd frontend
# 同时启动前端和Electron
pnpm run electron:dev
```

#### 构建桌面应用

```bash
cd frontend
# 构建并生成安装包
pnpm run electron:build

# 仅打包（不生成安装包）
pnpm run electron:pack
```

### 5. 访问应用

- **Web版本**: 打开浏览器访问 `http://localhost:5173`
- **桌面版本**: 运行构建的桌面应用或使用 `pnpm run electron:dev`

## 📖 使用说明

### 基本使用流程

1. **配置AI模型**

   - 在设置页面配置你的AI API密钥
   - 选择合适的AI模型（GPT-4、Claude、Gemini等）
2. **上传文件**

   - 支持拖拽上传或点击选择文件
   - 支持的格式：MP4、MP3、WAV、M4A等
3. **选择提示词**

   - 使用内置模板（学术、教程、会议纪要等）
   - 或创建自定义提示词
4. **生成笔记**

   - 系统自动提取字幕
   - AI生成结构化笔记
   - 实时显示处理进度
5. **管理笔记**

   - 查看历史笔记
   - 导出为Markdown格式
   - 删除不需要的笔记

### 高级功能

- **Whisper模型选择**: 根据需要选择不同精度的语音识别模型
- **多语言支持**: 支持中文、英文等多种语言的语音识别
- **批量处理**: 可以批量处理多个文件
- **自定义输出**: 支持自定义笔记格式和结构

## 📁 项目结构

```
video-note/
├── backend/                 # 后端代码
│   ├── app.py              # Flask应用入口
│   ├── config.py           # 配置文件
│   ├── requirements.txt    # Python依赖
│   ├── services/           # 业务逻辑服务
│   │   ├── ai_service.py   # AI服务
│   │   ├── whisper_service.py # Whisper服务
│   │   └── ai_config_service.py # AI配置服务
│   ├── utils/              # 工具类
│   │   ├── file_utils.py   # 文件处理工具
│   │   └── logger.py       # 日志工具
│   ├── models/             # 数据模型
│   ├── config/             # 配置文件
│   ├── data/               # 数据库文件
│   └── logs/               # 日志文件
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── services/       # API服务
│   │   ├── stores/         # 状态管理
│   │   ├── composables/    # Vue组合式函数
│   │   └── router/         # 路由配置
│   ├── electron/           # Electron桌面应用
│   │   ├── main.js         # 主进程
│   │   ├── preload.js      # 预加载脚本
│   │   └── config.js       # Electron配置
│   ├── package.json        # Node.js依赖
│   ├── vite.config.ts      # Vite配置
│   ├── electron-dev.js     # Electron开发启动脚本
│   ├── .env.electron       # Electron环境变量
│   ├── electron.d.ts       # Electron类型定义
│   └── ELECTRON.md         # Electron使用文档
├── Output/                 # 生成的笔记文件
├── Subtitles/              # 提取的字幕文件
├── Temp/                   # 临时文件
├── Prompts/                # 提示词模板
├── Model/                  # Whisper模型文件
└── Engine/                 # Whisper引擎
```

## 🔧 配置说明

### AI模型配置

支持的AI提供商和模型：

- **OpenAI**: GPT-3.5-turbo, GPT-4, GPT-4-turbo等
- **Anthropic**: Claude-3-haiku, Claude-3-sonnet, Claude-3-opus等
- **Google**: Gemini-pro, Gemini-1.5-pro等

### Whisper模型配置

支持的模型大小：

- **tiny**: 最快，精度较低
- **base**: 平衡速度和精度
- **small**: 较好精度
- **medium**: 更好精度
- **large**: 最高精度，速度较慢

### Electron桌面应用配置

桌面应用支持以下平台和格式：

- **Windows**: NSIS安装包 (.exe)
- **macOS**: DMG磁盘映像 (.dmg)
- **Linux**: AppImage (.AppImage) 和 Debian包 (.deb)

配置文件：
- `package.json` - 构建配置和依赖
- `electron/config.js` - 应用运行时配置
- `.env.electron` - 环境变量配置

详细配置说明请参考 `frontend/ELECTRON.md`

### 📥 Whisper下载链接

**引擎下载**：

- Windows独立版本：[whisper-standalone-win](https://github.com/Purfview/whisper-standalone-win/releases)
- 包含优化的CTranslate2实现，支持GPU加速

**模型下载**：

- Faster-Whisper模型集合：[Hugging Face模型库](https://huggingface.co/collections/Systran/faster-whisper-6867ecec0e757ee14896e2d3)
- 包含所有大小的预训练模型（tiny、base、small、medium、large等）

## 🐛 故障排除

### 常见问题

1. **文件上传失败**

   - 检查文件格式是否支持
   - 确认文件大小不超过限制
   - 检查磁盘空间是否充足
2. **字幕提取失败**

   - 确认Whisper模型已正确下载
   - 检查音频质量是否清晰
   - 尝试使用不同的模型大小

   ```
   git remote add origin git@github.com:Gaays/ai-note.git
   ```
3. **AI笔记生成失败**

   - 检查API密钥是否正确配置
   - 确认网络连接正常
   - 检查API配额是否充足

### 日志查看

- 后端日志：`backend/logs/app_YYYYMMDD.log`
- 前端控制台：浏览器开发者工具

## 📄 许可证

本项目采用GPL许可证。
