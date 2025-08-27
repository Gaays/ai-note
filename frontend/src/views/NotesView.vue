<script setup lang="ts">
import { ref, computed, onMounted, watch, onActivated } from "vue";
import { ElMessage, ElMessageBox, ElSteps, ElStep } from "element-plus";
import { useAppStore } from "../stores/app";
import { apiService } from "../services/api";
import {
  Upload,
  Download,
  FolderOpened,
  Refresh,
  ArrowRight,
  Document,
  Check,
  Star,
  Edit,
  Delete,
  View as Eye,
} from "@element-plus/icons-vue";
import type { UploadProps, UploadFile } from "element-plus";
import { marked } from "marked";

const appStore = useAppStore();

// 响应式数据
const uploadRef = ref();
const customPrompt = ref("");
const useCustomPrompt = ref(false);
const subtitlePreview = ref("");
const notePreview = ref("");
const showSubtitleDialog = ref(false);
const showNoteDialog = ref(false);
const previewSubtitleName = ref("");
const subtitleDialogScrollbar = ref();

// 历史笔记相关数据
interface HistoryNote {
  name: string;
  path: string;
  size: number;
  size_formatted: string;
  modified: string;
  extension: string;
}

interface NoteContentResponse {
  success: boolean;
  data: {
    content: string;
  };
  msg: string;
}

interface PromptFile {
  name: string;
  content: string;
}

interface SubtitleFile {
  name: string;
  path: string;
  size: number;
  size_formatted: string;
  modified: string;
}
// 历史笔记相关
const historyNotes = ref<HistoryNote[]>([]);
const selectedNote = ref<HistoryNote | null>(null);
const noteContent = ref("");
const loadingHistory = ref(false);
const loadingContent = ref(false);
const notePromptTags = ref<Record<string, string>>({});

// 提示词相关
const promptFiles = ref<PromptFile[]>([]);
const selectedPrompt = ref("");

// 提示词标识颜色生成
const generatePromptColors = (count: number): string[] => {
  const baseColors = [
    "#409EFF", // 蓝色
    "#67C23A", // 绿色
    "#E6A23C", // 橙色
    "#F56C6C", // 红色
    "#909399", // 灰色
    "#9C27B0", // 紫色
    "#00BCD4", // 青色
    "#FF9800", // 深橙色
    "#4CAF50", // 深绿色
    "#2196F3", // 深蓝色
    "#FF5722", // 深红色
    "#795548", // 棕色
  ];

  const colors: string[] = [];
  for (let i = 0; i < count; i++) {
    colors.push(baseColors[i % baseColors.length]);
  }
  return colors;
};

// 提示词颜色映射
const promptColorMap = computed(() => {
  const colors = generatePromptColors(promptFiles.value.length);
  const colorMap: Record<string, string> = {};
  promptFiles.value.forEach((prompt, index) => {
    colorMap[prompt.name] = colors[index];
  });
  return colorMap;
});

// 获取提示词颜色
const getPromptColor = (promptName: string): string => {
  return promptColorMap.value[promptName] || "#409EFF";
};

// 上传模式切换
const uploadMode = ref<"file" | "subtitle">("file");
const subtitleFiles = ref<SubtitleFile[]>([]);
const selectedSubtitleFile = ref("");
const selectedSubtitleContent = ref("");
const isLoadingSubtitles = ref(false);

// 步骤进度显示
interface ProcessStep {
  id: string;
  title: string;
  status: "pending" | "processing" | "completed" | "error";
  message?: string;
}

const processSteps = ref<ProcessStep[]>([]);
const showProcessSteps = ref(false);

// 步骤状态
const currentStep = ref(0);
const steps = ref([
  { title: "读取文件", status: "wait", description: "等待开始" },
  { title: "提取字幕", status: "wait", description: "等待开始" },
  { title: "生成笔记", status: "wait", description: "等待开始" },
]);

// 计算属性
const canExtractSubtitle = computed(() => appStore.hasFile && !appStore.loading);
const canGenerateNote = computed(
  () => (appStore.hasSubtitle || appStore.hasFile) && appStore.isAIConfigured && !appStore.loading
);
const fileInfo = computed(() => {
  if (!appStore.currentFile) return null;
  return {
    name: appStore.currentFile.name,
    size: (appStore.currentFile.size / 1024 / 1024).toFixed(2) + " MB",
    type: appStore.currentFile.type,
  };
});

// 文件上传前的检查
const beforeUpload: UploadProps["beforeUpload"] = (file) => {
  const isVideo = file.type.startsWith("video/") || file.type.startsWith("audio/");
  const isValidExt = /\.(mp4|avi|mov|mkv|mp3|wav|flac|m4a)$/i.test(file.name);

  if (!isVideo && !isValidExt) {
    ElMessage.error("请选择音视频文件！");
    return false;
  }

  const isLt500M = file.size / 1024 / 1024 < 500;
  if (!isLt500M) {
    ElMessage.error("文件大小不能超过 500MB！");
    return false;
  }

  return true;
};

// 文件选择处理
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    // 验证文件类型和大小
    const isValid = beforeUpload(file.raw);
    if (isValid) {
      handleFileUpload({ file: file.raw });
    }
  }
};

// 清除文件
const clearFile = () => {
  appStore.setCurrentFile(null);
  appStore.setCurrentFileId("");
  appStore.setSubtitleText("");
  appStore.setNoteContent("");
  uploadRef.value?.clearFiles();
  ElMessage.success("文件已清除");
};

// 文件上传
const handleFileUpload = async (options: any) => {
  const { file } = options;

  try {
    // 只保存文件引用，不立即上传到服务器
    appStore.setCurrentFile(file);
    ElMessage.success("文件选择成功！点击生成笔记开始处理");
  } catch (error: any) {
    ElMessage.error(`文件选择失败: ${error.message || error}`);
    appStore.setCurrentFile(null);
  }
};

// 步骤管理函数
const initializeSteps = () => {
  processSteps.value = [
    { id: "upload", title: "复制文件", status: "pending" },
    { id: "extract", title: "提取字幕", status: "pending" },
    { id: "generate", title: "生成笔记", status: "pending" },
  ];
  showProcessSteps.value = true;
};

const updateStepStatus = (
  stepType: "upload" | "extract" | "generate",
  status: "wait" | "process" | "finish" | "error",
  description: string
) => {
  const stepIndex = stepType === "upload" ? 0 : stepType === "extract" ? 1 : 2;
  steps.value[stepIndex].status = status;
  steps.value[stepIndex].description = description;

  // 更新当前步骤
  if (status === "process") {
    currentStep.value = stepIndex;
  } else if (status === "finish") {
    currentStep.value = stepIndex + 1;
  }
};

const resetSteps = () => {
  processSteps.value = [];
  showProcessSteps.value = false;
  // 重置步骤状态
  currentStep.value = 0;
  steps.value = [
    { title: "复制文件", status: "wait", description: "等待开始" },
    { title: "提取字幕", status: "wait", description: "等待开始" },
    { title: "生成笔记", status: "wait", description: "等待开始" },
  ];
};

// 提取字幕
const extractSubtitle = async () => {
  if (!appStore.currentFileId) {
    ElMessage.error("请先上传文件");
    return;
  }

  try {
    appStore.setLoading(true);

    const response = await apiService.extractSubtitle(
      appStore.currentFileId,
      appStore.currentWhisperModel
    );

    if (response.success) {
      appStore.setSubtitleText(response.data!.subtitle_text);
      ElMessage.success("字幕提取成功！");
    } else {
      throw new Error(response.msg);
    }
  } catch (error: any) {
    ElMessage.error(`字幕提取失败: ${error.message || error}`);
  } finally {
    appStore.setLoading(false);
  }
};

// AI笔记生成（自动提取字幕）
const generateNote = async () => {
  if (!appStore.isAIConfigured) {
    ElMessage.error("请先配置AI模型");
    return;
  }

  // 初始化步骤显示
  initializeSteps();

  try {
    appStore.setLoading(true);

    // 步骤1：如果是文件上传模式，先复制文件到temp目录
    if (uploadMode.value === "file") {
      if (!appStore.currentFile) {
        ElMessage.warning("请先选择文件");
        resetSteps();
        return;
      }

      // 开始复制文件
      updateStepStatus("upload", "process", "正在复制文件...");

      try {
        const response = await apiService.uploadFile(appStore.currentFile);

        if (response.success) {
          appStore.setCurrentFileId(response.data!.file_id);
          updateStepStatus("upload", "finish", "文件复制成功");
        } else {
          updateStepStatus("upload", "error", response.msg || "文件复制失败");
          ElMessage.error(response.msg || "文件复制失败");
          return;
        }
      } catch (error: any) {
        updateStepStatus("upload", "error", error.message || "文件复制失败");
        ElMessage.error(`文件复制失败: ${error.message || error}`);
        return;
      }
    } else {
      // 如果是字幕模式，直接标记复制步骤为完成
      updateStepStatus("upload", "finish", "无需复制文件");
    }

    // 步骤2：如果是文件上传模式且没有字幕，先提取字幕
    if (uploadMode.value === "file" && !appStore.subtitleText) {
      if (!appStore.hasFile) {
        ElMessage.warning("请先上传文件");
        resetSteps();
        return;
      }

      // 开始提取字幕
      updateStepStatus("extract", "process", "正在提取字幕...");

      try {
        const response = await apiService.extractSubtitle(
          appStore.currentFileId,
          appStore.currentWhisperModel
        );

        if (response.success) {
          appStore.setSubtitleText(response.data!.subtitle_text);
          updateStepStatus("extract", "finish", "字幕提取成功");
          
          // 字幕提取成功后删除临时文件
          if (appStore.currentFileId) {
            try {
              await apiService.deleteFile(appStore.currentFileId);
              console.log("临时文件删除成功");
            } catch (error) {
              console.error("删除临时文件失败:", error);
              // 不影响主流程，只记录错误
            }
          }
        } else {
          updateStepStatus("extract", "error", response.msg || "字幕提取失败");
          ElMessage.error(response.msg || "字幕提取失败");
          return;
        }
      } catch (error: any) {
        updateStepStatus("extract", "error", error.message || "字幕提取失败");
        ElMessage.error(`字幕提取失败: ${error.message || error}`);
        return;
      }
    } else if (appStore.subtitleText) {
      // 如果已有字幕，直接标记提取步骤为完成
      updateStepStatus("extract", "finish", "字幕已存在");
      
      // 如果是文件上传模式且有临时文件，需要删除临时文件
      if (uploadMode.value === "file" && appStore.currentFileId) {
        try {
          await apiService.deleteFile(appStore.currentFileId);
          console.log("临时文件删除成功（跳过字幕提取）");
        } catch (error) {
          console.error("删除临时文件失败:", error);
          // 不影响主流程，只记录错误
        }
      }
    }

    // 检查是否有字幕内容
    if (!appStore.subtitleText) {
      ElMessage.warning("请先选择字幕文件或上传视频文件");
      resetSteps();
      return;
    }

    // 步骤2：生成笔记
    updateStepStatus("generate", "process", "正在生成笔记...");

    let prompt = undefined;

    // 构建提示词
    if (useCustomPrompt.value && customPrompt.value) {
      prompt = customPrompt.value;
      // 如果同时选择了提示词选择器，将其添加到自定义提示词前
      if (selectedPrompt.value && selectedPrompt.value !== "default_note_prompt") {
        const selectedPromptFile = promptFiles.value.find((p) => p.name === selectedPrompt.value);
        if (selectedPromptFile) {
          prompt = `${selectedPromptFile.content}\n\n${prompt}`;
        }
      }
    } else if (selectedPrompt.value) {
      // 只使用选择的提示词
      const selectedPromptFile = promptFiles.value.find((p) => p.name === selectedPrompt.value);
      if (selectedPromptFile) {
        prompt = selectedPromptFile.content;
      }
    }

    // 确定原始文件路径
    let originalFilePath: string | undefined;
    if (uploadMode.value === "file" && appStore.currentFile) {
      originalFilePath = appStore.currentFile.name;
    } else if (uploadMode.value === "subtitle" && selectedSubtitleFile.value) {
      // 从字幕文件名中提取原始文件名（去掉时间戳部分）
      const subtitleName = selectedSubtitleFile.value.replace(".srt", "");
      const lastUnderscoreIndex = subtitleName.lastIndexOf("_");
      if (lastUnderscoreIndex > 0) {
        originalFilePath = subtitleName.substring(0, lastUnderscoreIndex);
      } else {
        originalFilePath = subtitleName;
      }
    }

    // 获取当前选择的提示词名称作为标识
    const promptTag = useCustomPrompt.value
      ? "自定义"
      : selectedPrompt.value || "default_note_prompt";

    const response = await apiService.generateNote(
      appStore.subtitleText,
      prompt,
      originalFilePath,
      promptTag
    );

    if (response.success) {
      appStore.setNoteContent(response.data!.note_content);
      updateStepStatus("generate", "finish", "笔记生成成功");

      // 临时文件已在字幕提取成功后删除

      // 自动刷新历史笔记列表
      await loadHistoryNotes();

      ElMessage.success("笔记生成成功！");

      // 延迟隐藏步骤条，然后显示笔记内容
      setTimeout(async () => {
        showProcessSteps.value = false;
        resetSteps();

        // 在步骤条隐藏后，自动打开当前生成的笔记
        const generatedNoteName = response.data!.filename || originalFilePath;
        const generatedNote = historyNotes.value.find((note) => note.name === generatedNoteName);
        if (generatedNote) {
          selectedNote.value = generatedNote;
          await viewNoteContent(generatedNote);
        }
      }, 2000);
    } else {
      updateStepStatus("generate", "error", response.msg || "笔记生成失败");
      throw new Error(response.msg);
    }
  } catch (error: any) {
    updateStepStatus("generate", "error", error.message || "笔记生成失败");
    ElMessage.error(`笔记生成失败: ${error.message || error}`);
  } finally {
    appStore.setLoading(false);
  }
};

// 预览字幕
const previewSubtitle = () => {
  subtitlePreview.value = appStore.subtitleText;
  previewSubtitleName.value = "当前字幕";
  showSubtitleDialog.value = true;
  // 确保对话框打开后滚动条回到顶部
  setTimeout(() => {
    if (subtitleDialogScrollbar.value) {
      subtitleDialogScrollbar.value.setScrollTop(0);
    }
  }, 100);
};

// 预览指定字幕文件
const previewSubtitleFile = async (filename: string) => {
  try {
    const response = await apiService.getSubtitleContent(filename);
    if (response.success) {
      subtitlePreview.value = response.content;
      previewSubtitleName.value = filename;
      showSubtitleDialog.value = true;
      // 确保对话框打开后滚动条回到顶部
      setTimeout(() => {
        if (subtitleDialogScrollbar.value) {
          subtitleDialogScrollbar.value.setScrollTop(0);
        }
      }, 100);
    } else {
      ElMessage.error(response.msg || "加载字幕内容失败");
    }
  } catch (error) {
    console.error("加载字幕内容失败:", error);
    ElMessage.error("加载字幕内容失败");
  }
};

// 预览笔记
const previewNote = () => {
  notePreview.value = appStore.noteContent;
  showNoteDialog.value = true;
};

// 保存笔记
const saveNote = async () => {
  if (!appStore.noteContent) {
    ElMessage.error("没有笔记内容可保存");
    return;
  }

  try {
    if (window.electronAPI) {
      const result = await window.electronAPI.saveNoteFile(
        `${appStore.currentFile?.name || "note"}.md`
      );
      if (!result.canceled && result.filePath) {
        // 这里可以调用后端API保存文件
        ElMessage.success("笔记保存成功！");
      }
    } else {
      // 浏览器环境下载
      const blob = new Blob([appStore.noteContent], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${appStore.currentFile?.name || "note"}.md`;
      a.click();
      URL.revokeObjectURL(url);
      ElMessage.success("笔记下载成功！");
    }
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.message || error}`);
  }
};

// 清空所有
const clearAll = async () => {
  try {
    await ElMessageBox.confirm("确定要清空所有内容吗？", "确认", {
      type: "warning",
    });

    appStore.clearAll();
    // 只有在未勾选自定义提示词时才清空自定义提示词内容
    if (!useCustomPrompt.value) {
      customPrompt.value = "";
      useCustomPrompt.value = false;
    }
    uploadRef.value?.clearFiles();

    ElMessage.success("已清空所有内容");
  } catch {
    // 用户取消
  }
};

// 加载历史笔记列表
const loadHistoryNotes = async () => {
  try {
    loadingHistory.value = true;
    const response = await apiService.getNotesHistory();
    if (response.success) {
      historyNotes.value = response.data!.sort(
        (a, b) => new Date(b.modified).getTime() - new Date(a.modified).getTime()
      );

      // 为每个笔记获取提示词标识
      for (const note of historyNotes.value) {
        try {
          const contentResponse = await apiService.getNoteContent(note.name);
          if (contentResponse.success) {
            notePromptTags.value[note.name] = extractPromptTag(contentResponse.content);
          }
        } catch (error) {
          console.error(`获取笔记 ${note.name} 的提示词标识失败:`, error);
          notePromptTags.value[note.name] = "未知";
        }
      }
    } else {
      ElMessage.error(`加载历史笔记失败: ${response.msg}`);
    }
  } catch (error: any) {
    ElMessage.error(`加载历史笔记失败: ${error.message || error}`);
  } finally {
    loadingHistory.value = false;
  }
};

// 加载提示词文件列表
const loadPromptFiles = async () => {
  try {
    const response = await apiService.getPrompts();
    if (response.success) {
      promptFiles.value = response.data || [];
      // 默认选择文件列表的第一个
      if (promptFiles.value.length > 0) {
        selectedPrompt.value = promptFiles.value[0].name;
      }
    } else {
      ElMessage.error(response.msg || "加载提示词列表失败");
    }
  } catch (error) {
    console.error("加载提示词列表失败:", error);
    ElMessage.error("加载提示词列表失败");
  }
};

// 加载字幕文件列表
const loadSubtitleFiles = async () => {
  isLoadingSubtitles.value = true;
  try {
    const response = await apiService.getSubtitles();
    if (response.success) {
      // 兼容所有字幕格式并按时间倒序排列
      const allSubtitles = (response.data || []).filter((file) => {
        const ext = file.name.toLowerCase().split(".").pop();
        return ["srt", "vtt", "ass", "ssa", "sub", "sbv", "lrc", "ttml", "dfxp"].includes(
          ext || ""
        );
      });

      // 按修改时间倒序排列
      subtitleFiles.value = allSubtitles.sort(
        (a, b) => new Date(b.modified).getTime() - new Date(a.modified).getTime()
      );
    } else {
      ElMessage.error(response.msg || "加载字幕文件列表失败");
    }
  } catch (error) {
    console.error("加载字幕文件列表失败:", error);
    ElMessage.error("加载字幕文件列表失败");
  } finally {
    isLoadingSubtitles.value = false;
  }
};

// 选择字幕文件
const selectSubtitleFile = async (filename: string) => {
  selectedSubtitleFile.value = filename;
  // 清除当前选中的笔记，确保不会同时显示步骤条和笔记内容
  selectedNote.value = null;
  noteContent.value = "";

  try {
    const response = await apiService.getSubtitleContent(filename);
    if (response.success) {
      selectedSubtitleContent.value = response.content;
      // 将字幕内容设置到应用状态中
      appStore.setSubtitleText(response.content);
      ElMessage.success("字幕文件加载成功");
    } else {
      ElMessage.error(response.msg || "加载字幕内容失败");
    }
  } catch (error) {
    console.error("加载字幕内容失败:", error);
    ElMessage.error("加载字幕内容失败");
  }
};

// 从笔记内容中提取提示词标识
const extractPromptTag = (content: string): string => {
  const match = content.match(/<!-- PROMPT_TAG: (.+?) -->/);
  return match ? match[1] : "未知";
};

// 查看笔记内容
const viewNoteContent = async (note: HistoryNote) => {
  try {
    loadingContent.value = true;
    selectedNote.value = note;
    // 确保在显示笔记内容时隐藏步骤条
    showProcessSteps.value = false;

    const response = await apiService.getNoteContent(note.name);
    if (response.success) {
      noteContent.value = marked(response.content);
    } else {
      ElMessage.error(`加载笔记内容失败: ${response.msg}`);
    }
  } catch (error: any) {
    ElMessage.error(`加载笔记内容失败: ${error.message || error}`);
  } finally {
    loadingContent.value = false;
  }
};

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

// 格式化字幕文件名，使其与笔记名称格式一致
const formatSubtitleName = (filename: string) => {
  // 移除文件扩展名
  const nameWithoutExt = filename.replace(/\.(srt|vtt|ass|ssa|sub|sbv|lrc|ttml|dfxp)$/i, "");

  // 查找最后一个下划线，分离源文件名和时间戳
  const lastUnderscoreIndex = nameWithoutExt.lastIndexOf("_");

  if (lastUnderscoreIndex > 0) {
    const sourceName = nameWithoutExt.substring(0, lastUnderscoreIndex);
    const timestamp = nameWithoutExt.substring(lastUnderscoreIndex + 1);

    // 格式化时间戳为更易读的格式
    if (timestamp.match(/^\d{8}_\d{6}$/)) {
      const year = timestamp.substring(0, 4);
      const month = timestamp.substring(4, 6);
      const day = timestamp.substring(6, 8);
      const hour = timestamp.substring(9, 11);
      const minute = timestamp.substring(11, 13);
      const second = timestamp.substring(13, 15);

      return `${sourceName} (${year}-${month}-${day} ${hour}:${minute}:${second})`;
    }

    return `${sourceName} (${timestamp})`;
  }

  // 如果没有找到下划线，返回原始名称
  return nameWithoutExt;
};

// 监听上传模式变化，切换时清除数据
watch(uploadMode, (newMode, oldMode) => {
  if (oldMode) {
    if (oldMode === "file" && newMode === "subtitle") {
      // 从文件上传切换到字幕选择，清除文件相关数据
      appStore.setCurrentFile(null);
      appStore.setCurrentFileId("");
      uploadRef.value?.clearFiles();
      // 自动刷新字幕文件列表
      loadSubtitleFiles();
    } else if (oldMode === "subtitle" && newMode === "file") {
      // 从字幕选择切换到文件上传，清除字幕选择相关数据
      selectedSubtitleFile.value = "";
      selectedSubtitleContent.value = "";
    }
    // 清除共同的数据
    appStore.setSubtitleText("");
    appStore.setNoteContent("");
    // 注意：不清除自定义提示词内容，因为用户可能希望在切换模式时保留自定义提示词
  }
});

// 检查AI配置状态
const checkAIConfiguration = async () => {
  try {
    const response = await apiService.getCurrentAIConfig();
    if (response.success && response.data) {
      // 更新应用状态中的AI配置
      appStore.setAIConfig(response.data);
    } else {
      // 如果没有当前配置，清空AI配置状态
      appStore.setAIConfig({ api_key: "", provider: "", model_name: "" });
    }
  } catch (error) {
    console.error("检查AI配置失败:", error);
    // 发生错误时也清空AI配置状态
    appStore.setAIConfig({ api_key: "", provider: "", model_name: "" });
  }
};

// 组件挂载时加载Whisper模型和历史笔记
onMounted(async () => {
  try {
    const response = await apiService.getWhisperModels();
    if (response.success) {
      appStore.setWhisperModels(response.data!);
    }
  } catch (error) {
    console.error("加载Whisper模型失败:", error);
  }

  // 检查AI配置状态
  await checkAIConfiguration();

  // 加载历史笔记
  await loadHistoryNotes();
  await loadPromptFiles();
  await loadSubtitleFiles();
});

// 页面激活时重新检查AI配置（从其他页面返回时）
onActivated(async () => {
  await checkAIConfiguration();
});
</script>

<template>
  <div class="notes-layout">
    <!-- 左侧主要功能区域 -->
    <div class="left-panel">
      <el-scrollbar height="100%">
        <div class="notes-container">
          <!-- 文件上传区域 -->
          <el-card class="upload-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div>
                  <el-icon><Upload /></el-icon>
                  <span>{{ uploadMode === "file" ? "文件上传" : "选择字幕" }}</span>
                </div>
                <el-radio-group v-model="uploadMode" size="small">
                  <el-radio-button label="file">文件上传</el-radio-button>
                  <el-radio-button label="subtitle">已解析字幕</el-radio-button>
                </el-radio-group>
              </div>
            </template>

            <!-- 文件上传模式 -->
            <div v-if="uploadMode === 'file'" class="upload-area">
              <el-upload
                ref="uploadRef"
                class="upload-dragger"
                drag
                :auto-upload="false"
                :on-change="handleFileChange"
                :before-upload="() => false"
                accept=".mp4,.avi,.mov,.mkv,.flv,.wmv,.webm,.m4v,.3gp,.mp3,.wav,.flac,.aac,.ogg,.wma,.m4a"
              >
                <el-icon class="el-icon--upload"><Upload /></el-icon>
                <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持视频格式：MP4, AVI, MOV, MKV, FLV, WMV, WebM, M4V, 3GP<br />
                    支持音频格式：MP3, WAV, FLAC, AAC, OGG, WMA, M4A
                  </div>
                </template>
              </el-upload>
            </div>

            <!-- 字幕文件选择模式 -->
            <div v-else class="subtitle-selection">
              <div v-loading="isLoadingSubtitles" class="subtitle-list">
                <el-scrollbar height="400px">
                  <div v-if="subtitleFiles.length === 0" class="empty-state">
                    <el-empty description="暂无已解析的字幕文件" />
                  </div>
                  <div v-else class="subtitle-files">
                    <div
                      v-for="file in subtitleFiles"
                      :key="file.name"
                      class="subtitle-item"
                      :class="{ active: selectedSubtitleFile === file.name }"
                      @click="selectSubtitleFile(file.name)"
                    >
                      <div class="subtitle-info">
                        <div class="subtitle-name" :title="file.name">
                          {{ formatSubtitleName(file.name) }}
                        </div>
                        <div class="subtitle-meta">
                          <span class="subtitle-size">{{ file.size_formatted }}</span>
                          <span class="subtitle-time">{{ formatDate(file.modified) }}</span>
                        </div>
                      </div>
                      <div class="subtitle-actions">
                        <el-icon v-if="selectedSubtitleFile === file.name" class="selected-icon">
                          <Check />
                        </el-icon>
                        <el-icon
                          class="preview-icon"
                          :size="16"
                          @click.stop="previewSubtitleFile(file.name)"
                          :title="`预览 ${file.name}`"
                        >
                          <Eye />
                        </el-icon>
                      </div>
                    </div>
                  </div>
                </el-scrollbar>
              </div>
            </div>
          </el-card>

          <!-- AI笔记生成区域 -->
          <el-card class="note-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Edit /></el-icon>
                <span>AI笔记生成</span>
              </div>
            </template>

            <!-- 提示词配置 -->
            <div class="prompt-section">
              <!-- 提示词选择器 -->
              <div class="prompt-selector">
                <el-form-item label="选择提示词：">
                  <el-select
                    v-model="selectedPrompt"
                    placeholder="请选择提示词"
                    style="width: 200px"
                  >
                    <el-option
                      v-for="prompt in promptFiles"
                      :key="prompt.name"
                      :label="prompt.name"
                      :value="prompt.name"
                    />
                  </el-select>
                </el-form-item>
              </div>

              <el-checkbox v-model="useCustomPrompt">使用自定义提示词</el-checkbox>

              <el-input
                v-if="useCustomPrompt"
                v-model="customPrompt"
                type="textarea"
                :rows="3"
                placeholder="请输入自定义提示词，例如：请帮我总结这段音频的主要内容，并提取关键信息..."
                class="prompt-input"
              />
            </div>

            <!-- 生成按钮 -->
            <div class="note-actions">
              <el-button
                class="generate-note-btn"
                type="primary"
                size="default"
                :disabled="!canGenerateNote"
                :loading="appStore.loading"
                @click="generateNote"
              >
                <el-icon><Star /></el-icon>
                生成笔记
              </el-button>

              <el-button v-if="appStore.hasNote" type="warning" size="default" @click="saveNote">
                <el-icon><Download /></el-icon>
                下载笔记
              </el-button>
            </div>

            <!-- 笔记状态 -->
            <div v-if="appStore.hasNote" class="note-status">
              <el-alert
                title="笔记生成完成"
                type="success"
                :description="`笔记长度: ${appStore.noteContent.length} 字符`"
                show-icon
                :closable="false"
              />
            </div>

            <!-- AI配置提示 -->
            <div v-if="!appStore.isAIConfigured" class="ai-config-tip">
              <el-alert
                title="请先配置AI模型"
                type="warning"
                description="请前往设置页面配置AI模型API密钥"
                show-icon
                :closable="false"
              >
                <template #default>
                  <el-button type="text" size="default" @click="$router.push('/settings')"
                    >前往设置</el-button
                  >
                </template>
              </el-alert>
            </div>
          </el-card>

          <!-- 操作区域 -->
          <!-- <el-card class="actions-card" shadow="hover">
            <div class="global-actions">
              <el-button type="danger" @click="clearAll">
                <el-icon><Delete /></el-icon>
                清空所有
              </el-button>
            </div>
          </el-card> -->
        </div>
      </el-scrollbar>
    </div>
    <div class="right-panel">
      <div class="history-layout">
        <!-- 左侧：历史笔记列表 -->
        <div class="history-sidebar">
          <el-card class="history-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div>
                  <el-icon><FolderOpened /></el-icon>
                  <span>历史笔记</span>
                </div>
                <el-button
                  type="primary"
                  size="small"
                  @click="loadHistoryNotes"
                  :loading="loadingHistory"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>

            <!-- 笔记列表 -->
            <div class="history-list">
              <el-scrollbar height="calc(100vh - 200px)">
                <div v-if="loadingHistory" class="loading-placeholder">
                  <el-skeleton :rows="5" animated />
                </div>
                <div v-else-if="historyNotes.length === 0" class="empty-placeholder">
                  <el-empty description="暂无历史笔记" />
                </div>
                <div v-else>
                  <div
                    v-for="note in historyNotes"
                    :key="note.name"
                    class="note-item"
                    :class="{ active: selectedNote?.name === note.name }"
                    @click="viewNoteContent(note)"
                  >
                    <div class="note-info">
                      <div class="note-header">
                        <div class="note-name" :title="note.name">{{ note.name }}</div>
                      </div>
                      <div class="note-meta">
                        <span class="note-size">{{ note.size_formatted }}</span>
                        <span class="note-date">{{ formatDate(note.modified) }}</span>
                        <el-tag
                          v-if="notePromptTags[note.name]"
                          :color="getPromptColor(notePromptTags[note.name])"
                          size="small"
                          class="prompt-tag"
                        >
                          {{ notePromptTags[note.name] }}
                        </el-tag>
                      </div>
                    </div>
                    <el-icon class="note-arrow"><ArrowRight /></el-icon>
                  </div>
                </div>
              </el-scrollbar>
            </div>
          </el-card>
        </div>

        <!-- 右侧：笔记内容展示 -->
        <div class="content-area">
          <el-card class="content-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon><Document /></el-icon>
                  <span>{{ selectedNote ? selectedNote.name : "笔记内容" }}</span>
                  <el-tag
                    v-if="selectedNote && notePromptTags[selectedNote.name]"
                    :color="getPromptColor(notePromptTags[selectedNote.name])"
                    size="small"
                    class="prompt-tag"
                  >
                    {{ notePromptTags[selectedNote.name] }}
                  </el-tag>
                </div>
              </div>
            </template>

            <div class="note-content">
              <el-scrollbar height="calc(100vh - 200px)">
                <!-- 步骤进度显示 -->
                <div v-if="showProcessSteps" class="steps-container">
                  <el-steps
                    :active="currentStep"
                    finish-status="success"
                    process-status="process"
                    :space="200"
                  >
                    <el-step
                      v-for="(step, index) in steps"
                      :key="index"
                      :title="step.title"
                      :description="step.description"
                      :status="step.status"
                    />
                  </el-steps>
                </div>

                <div v-if="loadingContent" class="loading-placeholder">
                  <el-skeleton :rows="10" animated />
                </div>
                <div v-else-if="!selectedNote && !showProcessSteps" class="empty-placeholder">
                  <el-empty description="请选择一个笔记查看内容" />
                </div>
                <div v-else-if="selectedNote" class="markdown-content" v-html="noteContent"></div>
              </el-scrollbar>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>

  <!-- 字幕预览对话框 -->
  <el-dialog
    v-model="showSubtitleDialog"
    :title="`字幕预览 - ${previewSubtitleName}`"
    width="60%"
    :before-close="() => (showSubtitleDialog = false)"
  >
    <el-scrollbar ref="subtitleDialogScrollbar" height="400px">
      <pre class="subtitle-content">{{ subtitlePreview }}</pre>
    </el-scrollbar>
  </el-dialog>

  <!-- 笔记预览对话框 -->
  <el-dialog v-model="showNoteDialog" width="70%" :before-close="() => (showNoteDialog = false)">
    <template #header>
      <div class="dialog-header">
        <span>笔记预览</span>
        <el-tag
          v-if="extractPromptTag(notePreview)"
          :color="getPromptColor(extractPromptTag(notePreview))"
          class="prompt-tag"
          size="small"
        >
          {{ extractPromptTag(notePreview) }}
        </el-tag>
      </div>
    </template>
    <el-input v-model="notePreview" type="textarea" :rows="20" readonly class="preview-textarea" />
    <template #footer>
      <el-button type="primary" @click="saveNote">
        <el-icon><Download /></el-icon>
        保存笔记
      </el-button>
    </template>
  </el-dialog>
</template>

<style lang="scss" scoped>
@import "@/assets/mixins.scss";

.notes-layout {
  display: flex;
  height: 100%;
  background: $background-light;
  overflow: hidden;
}

.left-panel {
  flex: 1;
  padding: 20px;
  max-width: 400px;
  height: 100%;
}

.right-panel {
  flex: 1;
  padding: 20px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  overflow-y: auto;
  min-width: 500px;
}

.notes-container {
  max-width: none;
  margin: 0;
  padding: 0;
  background: none;
  min-height: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  justify-content: space-between;
}

.card-header > div:first-child {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.prompt-tag {
  font-size: 12px;
  border: none;
  color: white !important;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.upload-card {
  border: 2px dashed #dcdfe6;
  transition: border-color 0.3s;
  :deep(.el-card__body) {
    padding: 0;
  }

  .upload-area {
    padding: 20px;
    margin-bottom: 60px;

    .upload-dragger {
      width: 100%;
      height: 180px;

      .el-icon--upload {
        font-size: 48px;
        color: #409eff;
        margin-bottom: 16px;
      }

      .el-upload__text {
        font-size: 16px;
        color: #fff;
      }
    }
  }

  .subtitle-selection {
    padding: 20px;

    .subtitle-list {
      min-height: 200px;

      .empty-state {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
      }

      .subtitle-files {
        overflow-x: hidden;
        .subtitle-item {
          padding: 12px;
          border: 1px solid #e4e7ed;
          border-radius: 6px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.3s;
          display: flex;
          justify-content: space-between;
          align-items: center;
          overflow: hidden;
          width: 100%;
          position: relative;

          &:hover {
            border-color: #00d4ff;
            background-color: rgba(0, 212, 255, 0.1);

            .preview-icon {
              opacity: 1;
              visibility: visible;
            }
          }

          &.active {
            border-color: #00d4ff;
            background-color: rgba(0, 212, 255, 0.2);
          }

          .subtitle-info {
            flex: 1;
            overflow: hidden;

            .subtitle-name {
              font-weight: 500;
              color: #303133;
              margin-bottom: 4px;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }

            .subtitle-meta {
              display: flex;
              gap: 12px;
              font-size: 12px;
              color: #909399;

              .subtitle-size {
                &::before {
                  content: "📄 ";
                }
              }

              .subtitle-time {
                &::before {
                  content: "🕒 ";
                }
              }
            }
          }

          .subtitle-actions {
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .selected-icon {
            color: #409eff;
            font-size: 18px;
          }

          .preview-icon {
            color: #909399;
            font-size: 16px;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            border-radius: 4px;

            &:hover {
              color: #409eff;
              background-color: rgba(64, 158, 255, 0.1);
            }
          }
        }
      }
    }
  }
}

.upload-card:hover {
  border-color: #409eff;
}

.upload-dragger {
  width: 100%;
}

.file-info {
  margin-top: 16px;
}

.subtitle-actions {
  margin-bottom: 16px;
}

.model-select {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}

.subtitle-status,
.note-status,
.ai-config-tip {
  margin-top: 16px;
}

.prompt-section {
  margin-bottom: 20px;
}

.prompt-input {
  margin-top: 12px;
}

.note-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 0;
}

// AI科技风生成笔记按钮
.generate-note-btn {
  @include gradient-button;
  width: 100% !important;
  height: 48px !important;
  font-size: 16px !important;

  // 覆盖Element Plus的默认样式
  &.el-button {
    background: $gradient-primary !important;
    border: none !important;
    color: $text-primary !important;

    &:hover {
      background: $gradient-primary !important;
    }

    &:focus {
      background: $gradient-primary !important;
    }
  }

  .el-icon {
    margin-right: 8px;
    font-size: 18px;
  }
}

.global-actions {
  text-align: center;
}

.preview-textarea {
  font-family: "Courier New", monospace;
}

.subtitle-content {
  font-family: "Courier New", monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 0;
}

/* 历史笔记样式 */
.history-layout {
  display: flex;
  height: 100%;
  gap: 20px;
  padding: 0;
}

.history-list {
}

.history-sidebar {
  flex: 0 0 350px;
  min-width: 300px;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.history-card,
.content-card {
  height: 100%;
}

.note-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.note-item:hover {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

.note-item.active {
  background: rgba(64, 158, 255, 0.2);
  border-color: #409eff;
}

.note-info {
  width: 100%;
  overflow: hidden;
}

.note-name {
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.note-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.note-arrow {
  color: #c0c4cc;
  transition: color 0.3s ease;
}

.note-item:hover .note-arrow {
  color: #409eff;
}

.loading-placeholder,
.empty-placeholder {
  padding: 20px;
  text-align: center;
}

// 步骤进度显示样式
.steps-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  min-height: calc(100vh - 400px);
  height: 100%;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.markdown-content {
  padding: 16px;
  line-height: 1.8;
  color: #fff;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: #409eff;
  margin-top: 24px;
  margin-bottom: 16px;
}

.markdown-content p {
  margin-bottom: 16px;
}

.markdown-content ul,
.markdown-content ol {
  margin-bottom: 16px;
  padding-left: 24px;
}

.markdown-content li {
  margin-bottom: 8px;
}

.markdown-content code {
  background: rgba(30, 41, 59, 0.8);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "Courier New", monospace;
  color: #00d4ff;
}

.markdown-content pre {
  background: rgba(30, 41, 59, 0.8);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.markdown-content blockquote {
  border-left: 4px solid #409eff;
  padding-left: 16px;
  margin: 16px 0;
  color: #fff;
  font-style: italic;
}

/* 表单文字不换行 */
.el-text,
.card-header span,
.note-name,
.note-meta span {
  white-space: nowrap;
}

.model-select .el-text {
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .history-sidebar {
    flex: 0 0 300px;
    min-width: 250px;
  }
}

@media (max-width: 1200px) {
  .left-panel {
    min-width: 500px;
  }

  .right-panel {
    min-width: 400px;
  }

  .history-sidebar {
    flex: 0 0 280px;
    min-width: 220px;
  }
}

@media (max-width: 768px) {
  .notes-layout {
    flex-direction: column;
    height: auto;
  }

  .left-panel,
  .right-panel {
    flex: none;
    min-width: auto;
    padding: 15px;
  }

  .history-layout {
    flex-direction: column;
    height: auto;
  }

  .history-sidebar,
  .content-area {
    flex: none;
    min-width: auto;
  }

  .history-card,
  .content-card {
    height: 400px;
  }

  .notes-container {
    gap: 16px;
  }

  .subtitle-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .action-buttons {
    justify-content: center;
  }

  .note-actions {
    justify-content: center;
  }
}
</style>
