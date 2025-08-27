# Electron 配置说明

本文档详细说明了 AI Note Generator 项目的 Electron 配置和使用方法。

## 📁 项目结构

```
frontend/
├── electron/                 # Electron 主进程文件
│   ├── main.js              # 主进程入口文件
│   ├── preload.js           # 预加载脚本
│   └── config.js            # Electron 配置文件
├── scripts/                 # 构建和开发脚本
│   └── electron-dev.js      # 开发环境启动脚本
├── src/
│   ├── types/
│   │   └── electron.d.ts    # Electron API 类型定义
│   └── composables/
│       └── useElectron.ts   # Electron API 组合式函数
├── .env.electron            # Electron 环境变量配置
└── package.json             # 包含 Electron 构建配置
```

## ⚙️ 配置文件说明

### 1. package.json 构建配置

```json
{
  "build": {
    "appId": "com.gaays.ai-note",
    "productName": "AI Note Generator",
    "directories": {
      "output": "dist-electron"
    },
    "files": [
      "dist/**/*",
      "electron/**/*",
      "node_modules/**/*"
    ],
    "extraResources": [
      {
        "from": "../backend",
        "to": "backend",
        "filter": ["**/*", "!**/__pycache__", "!**/.*"]
      }
    ]
  }
}
```

### 2. electron/config.js

统一管理开发和生产环境的配置，包括：
- 后端服务配置
- 窗口设置
- 文件路径
- 支持的文件格式
- 默认设置

### 3. .env.electron

环境变量配置文件，包含应用名称、版本、端口等配置。

## 🚀 开发和构建

### 开发环境

```bash
# 启动开发环境（同时启动 Vite 和 Electron）
pnpm run electron:dev

# 仅启动 Vite 开发服务器
pnpm run dev

# 仅启动 Electron（需要先启动 Vite）
pnpm run electron
```

### 生产构建

```bash
# 构建应用（生成安装包）
pnpm run electron:build

# 构建应用（仅打包，不生成安装包）
pnpm run electron:pack

# 构建应用（不发布）
pnpm run electron:dist

# 清理构建文件
pnpm run electron:clean
```

### 其他命令

```bash
# 安装应用依赖
pnpm run postinstall

# 重新构建原生模块
pnpm run rebuild
```

## 🔧 主要功能

### 1. 后端服务管理

- 自动启动 Python 后端服务
- 监控后端服务状态
- 支持手动启动/停止后端服务

### 2. 文件系统操作

- 文件读写操作
- 目录创建
- 文件存在性检查
- 预设的文件选择器

### 3. 窗口管理

- 窗口最小化、最大化、关闭
- 应用重启
- 自定义窗口大小和行为

### 4. 系统集成

- 打开外部链接
- 系统对话框
- 平台检测
- 应用信息获取

## 📝 API 使用示例

### 在 Vue 组件中使用

```vue
<template>
  <div>
    <button @click="selectVideo">选择视频文件</button>
    <button @click="startBackend">启动后端服务</button>
    <p>后端状态: {{ backendStatus.running ? '运行中' : '已停止' }}</p>
  </div>
</template>

<script setup lang="ts">
import { useElectron } from '@/composables/useElectron'

const { 
  backendStatus, 
  startBackend, 
  fileOperations 
} = useElectron()

const selectVideo = async () => {
  const result = await fileOperations.selectVideoFile()
  if (!result.canceled && result.filePaths.length > 0) {
    console.log('选择的文件:', result.filePaths[0])
  }
}
</script>
```

### 直接使用 Electron API

```typescript
// 检查是否在 Electron 环境中
if (window.electronAPI) {
  // 获取应用信息
  const appInfo = await window.electronAPI.getAppInfo()
  
  // 启动后端服务
  const result = await window.electronAPI.startBackend()
  
  // 选择文件
  const fileResult = await window.electronAPI.selectVideoFile()
}
```

## 🔒 安全性

### 1. 上下文隔离

- 启用 `contextIsolation: true`
- 禁用 `nodeIntegration: false`
- 使用 preload 脚本安全地暴露 API

### 2. 预加载脚本

通过 `preload.js` 安全地暴露必要的 API 给渲染进程，避免直接暴露 Node.js API。

### 3. IPC 通信

使用 `ipcMain.handle` 和 `ipcRenderer.invoke` 进行安全的进程间通信。

## 🐛 故障排除

### 1. 后端服务启动失败

- 检查 Python 环境是否正确安装
- 确认后端依赖是否已安装
- 查看控制台错误信息

### 2. 文件路径问题

- 开发环境和生产环境的路径不同
- 使用 `config.js` 中的路径配置
- 检查 `extraResources` 配置是否正确

### 3. 构建问题

- 清理构建缓存：`pnpm run electron:clean`
- 重新安装依赖：`pnpm install`
- 重新构建原生模块：`pnpm run rebuild`

### 4. 权限问题

- 确保应用有足够的文件系统权限
- 在 macOS 上可能需要额外的权限配置

## 📦 打包配置

### Windows

- 使用 NSIS 安装程序
- 支持自定义安装目录
- 创建桌面和开始菜单快捷方式

### macOS

- 生成 DMG 安装包
- 支持代码签名（需要开发者证书）

### Linux

- 生成 AppImage 格式
- 支持多种 Linux 发行版

## 🔄 更新机制

项目已配置 electron-builder，支持自动更新功能。要启用自动更新：

1. 配置更新服务器
2. 设置代码签名
3. 在主进程中集成 electron-updater

## 📚 相关文档

- [Electron 官方文档](https://www.electronjs.org/docs)
- [electron-builder 文档](https://www.electron.build/)
- [Vue 3 文档](https://vuejs.org/)
- [Vite 文档](https://vitejs.dev/)