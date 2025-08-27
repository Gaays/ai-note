<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 历史记录接口
interface HistoryItem {
  id: string
  filename: string
  original_file: string
  subtitle_file: string
  note_file: string
  created_at: string
  file_size: number
  duration?: number
  ai_model: string
  whisper_model: string
}

// 响应式数据
const loading = ref(false)
const historyList = ref<HistoryItem[]>([])
const selectedItems = ref<string[]>([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const showNoteDialog = ref(false)
const currentNoteContent = ref('')
const currentNoteTitle = ref('')

// 模拟历史数据（实际应该从后端API获取）
const mockHistoryData: HistoryItem[] = [
  {
    id: '1',
    filename: '机器学习入门课程.mp4',
    original_file: '/uploads/机器学习入门课程.mp4',
    subtitle_file: '/subtitles/机器学习入门课程.srt',
    note_file: '/output/机器学习入门课程_笔记.md',
    created_at: '2024-01-15T10:30:00Z',
    file_size: 157286400, // 150MB
    duration: 3600, // 1小时
    ai_model: 'gpt-4',
    whisper_model: 'medium'
  },
  {
    id: '2',
    filename: '深度学习原理讲解.mp4',
    original_file: '/uploads/深度学习原理讲解.mp4',
    subtitle_file: '/subtitles/深度学习原理讲解.srt',
    note_file: '/output/深度学习原理讲解_笔记.md',
    created_at: '2024-01-14T15:45:00Z',
    file_size: 209715200, // 200MB
    duration: 4500, // 1.25小时
    ai_model: 'gpt-3.5-turbo',
    whisper_model: 'large'
  },
  {
    id: '3',
    filename: 'Python编程基础.mp3',
    original_file: '/uploads/Python编程基础.mp3',
    subtitle_file: '/subtitles/Python编程基础.srt',
    note_file: '/output/Python编程基础_笔记.md',
    created_at: '2024-01-13T09:20:00Z',
    file_size: 52428800, // 50MB
    duration: 2700, // 45分钟
    ai_model: 'claude-3-sonnet',
    whisper_model: 'base'
  }
]

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 格式化相对时间
const formatRelativeTime = (dateString: string): string => {
  return formatDistanceToNow(new Date(dateString), {
    addSuffix: true,
    locale: zhCN
  })
}

// 加载历史记录
const loadHistory = async () => {
  try {
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 过滤搜索结果
    let filteredData = mockHistoryData
    if (searchKeyword.value) {
      filteredData = mockHistoryData.filter(item => 
        item.filename.toLowerCase().includes(searchKeyword.value.toLowerCase())
      )
    }
    
    // 分页
    total.value = filteredData.length
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    historyList.value = filteredData.slice(start, end)
    
  } catch (error: any) {
    ElMessage.error(`加载历史记录失败: ${error.message || error}`)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadHistory()
}

// 查看笔记
const viewNote = async (item: HistoryItem) => {
  try {
    loading.value = true
    
    // 模拟读取笔记内容
    await new Promise(resolve => setTimeout(resolve, 300))
    
    currentNoteTitle.value = item.filename
    currentNoteContent.value = `# ${item.filename} - 学习笔记

## 概述
这是一个关于${item.filename}的学习笔记，使用${item.ai_model}模型生成。

## 主要内容

### 1. 核心概念
- 重要概念A：详细解释...
- 重要概念B：详细解释...
- 重要概念C：详细解释...

### 2. 关键知识点
1. **知识点1**：具体内容和解释
2. **知识点2**：具体内容和解释
3. **知识点3**：具体内容和解释

### 3. 实践要点
- 实践建议1
- 实践建议2
- 实践建议3

## 总结
通过本次学习，我们了解了...这些知识点对于...具有重要意义。

---
*笔记生成时间：${new Date(item.created_at).toLocaleString()}*
*使用模型：${item.ai_model} + ${item.whisper_model}*`
    
    showNoteDialog.value = true
  } catch (error: any) {
    ElMessage.error(`读取笔记失败: ${error.message || error}`)
  } finally {
    loading.value = false
  }
}

// 下载文件
const downloadFile = async (item: HistoryItem, type: 'subtitle' | 'note') => {
  try {
    const filename = type === 'subtitle' 
      ? item.filename.replace(/\.[^/.]+$/, '.srt')
      : item.filename.replace(/\.[^/.]+$/, '_笔记.md')
    
    // 模拟文件内容
    let content = ''
    if (type === 'subtitle') {
      content = `1\n00:00:00,000 --> 00:00:05,000\n欢迎来到${item.filename}\n\n2\n00:00:05,000 --> 00:00:10,000\n今天我们将学习...`
    } else {
      content = currentNoteContent.value || `# ${item.filename} - 学习笔记\n\n这是${item.filename}的学习笔记内容...`
    }
    
    // 创建下载
    const blob = new Blob([content], { type: type === 'subtitle' ? 'text/plain' : 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success(`${type === 'subtitle' ? '字幕' : '笔记'}下载成功！`)
  } catch (error: any) {
    ElMessage.error(`下载失败: ${error.message || error}`)
  }
}

// 删除记录
const deleteItems = async (ids: string[]) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${ids.length} 条记录吗？删除后无法恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    loading.value = true
    
    // 模拟删除API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 从列表中移除
    historyList.value = historyList.value.filter(item => !ids.includes(item.id))
    selectedItems.value = []
    
    ElMessage.success(`成功删除 ${ids.length} 条记录`)
    
    // 重新加载数据
    loadHistory()
  } catch {
    // 用户取消删除
  } finally {
    loading.value = false
  }
}

// 批量删除
const batchDelete = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }
  deleteItems(selectedItems.value)
}

// 单个删除
const deleteItem = (id: string) => {
  deleteItems([id])
}

// 页面变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadHistory()
}

// 页面大小变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadHistory()
}

// 选择变化
const handleSelectionChange = (selection: HistoryItem[]) => {
  selectedItems.value = selection.map(item => item.id)
}

// 组件挂载时加载数据
onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="history-container">
    <!-- 搜索和操作栏 -->
    <el-card class="search-card">
      <div class="search-bar">
        <div class="search-input">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文件名..."
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </div>
        <div class="action-buttons">
          <el-button
            type="danger"
            :disabled="selectedItems.length === 0"
            @click="batchDelete"
          >
            <el-icon><Delete /></el-icon>
            批量删除 ({{ selectedItems.length }})
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 历史记录表格 -->
    <el-card class="table-card" v-loading="loading">
      <el-table
        :data="historyList"
        @selection-change="handleSelectionChange"
        style="width: 100%"
        empty-text="暂无历史记录"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-info">
              <div class="filename">{{ row.filename }}</div>
              <div class="file-meta">
                <el-tag size="small" type="info">{{ formatFileSize(row.file_size) }}</el-tag>
                <el-tag size="small" type="success" v-if="row.duration">
                  {{ formatDuration(row.duration) }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="AI模型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.ai_model }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="Whisper模型" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="warning">{{ row.whisper_model }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="150">
          <template #default="{ row }">
            <div class="time-info">
              <div>{{ new Date(row.created_at).toLocaleDateString() }}</div>
              <div class="relative-time">{{ formatRelativeTime(row.created_at) }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" type="primary" @click="viewNote(row)">
                查看笔记
              </el-button>
              <el-dropdown>
                <el-button size="small">
                  下载<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="downloadFile(row, 'subtitle')">
                      下载字幕
                    </el-dropdown-item>
                    <el-dropdown-item @click="downloadFile(row, 'note')">
                      下载笔记
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button size="small" type="danger" @click="deleteItem(row.id)">
                删除
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 笔记预览对话框 -->
    <el-dialog
      v-model="showNoteDialog"
      title="笔记预览"
      width="70%"
      :before-close="() => (showNoteDialog = false)"
    >
      <div class="note-preview">
        <el-scrollbar height="500px">
          <div v-if="loadingNoteContent" class="loading-placeholder">
            <el-skeleton :rows="10" animated />
          </div>
          <div v-else class="note-content" v-html="noteContent"></div>
        </el-scrollbar>
      </div>
      <template #footer>
        <el-button type="primary" @click="saveNote">
          <el-icon><Download /></el-icon>
          保存笔记
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 16px;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.search-input {
  flex: 1;
  max-width: 400px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.table-card {
  min-height: 400px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filename {
  font-weight: 500;
  color: #e2e8f0;
}

.file-meta {
  display: flex;
  gap: 4px;
}

.time-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.relative-time {
  font-size: 12px;
  color: rgba(226, 232, 240, 0.7);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.note-preview {
  padding: 16px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.8);
}

.note-content {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  line-height: 1.6;
  color: #e2e8f0;
}

:deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  line-height: 1.6;
}
</style>