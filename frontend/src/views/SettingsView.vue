<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useAppStore } from "../stores/app";
import { apiService } from "../services/api";
import type { AIModelConfig, WhisperModel } from "../services/api";

const appStore = useAppStore();

// 响应式数据
const loading = ref(false);
const testingConnection = ref(false);
const whisperModels = ref<WhisperModel[]>([]);
const selectedWhisperModel = ref("");

// AI配置列表管理
const aiConfigs = ref<AIModelConfig[]>([]);
const currentConfig = ref<AIModelConfig | null>(null);
const showConfigDialog = ref(false);
const editingConfig = ref<AIModelConfig | null>(null);
const isCreating = ref(false);

// 配置表单数据
const configForm = ref<Omit<AIModelConfig, 'id' | 'created_at' | 'updated_at'>>({
  name: '',
  provider: 'openai',
  api_key: '',
  model_name: 'gpt-3.5-turbo',
  base_url: ''
});

// 测试配置数据（用于独立测试）
const testConfig = ref<AIModelConfig>({
  name: '',
  provider: 'openai',
  api_key: '',
  model_name: 'gpt-3.5-turbo',
  base_url: ''
});

// AI提供商选项
const aiProviders = [
  { label: "OpenAI", value: "openai" },
  { label: "Anthropic (Claude)", value: "anthropic" },
  { label: "Google (Gemini)", value: "gemini" },
  { label: "自定义", value: "custom" },
];

// 模型选项
const modelOptions = {
  openai: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
  anthropic: [
    "claude-3-haiku-20240307",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-5-sonnet-20241022",
  ],
  gemini: ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"],
  custom: [],
};

// AI配置列表管理方法
const loadAIConfigs = async () => {
  try {
    loading.value = true;
    const response = await apiService.getAllAIConfigs();
    if (response.success && response.data) {
      aiConfigs.value = response.data;
    } else {
      aiConfigs.value = [];
    }
    
    // 获取当前配置
    const currentResponse = await apiService.getCurrentAIConfig();
    if (currentResponse.success && currentResponse.data) {
      currentConfig.value = currentResponse.data;
    } else {
      currentConfig.value = null;
    }
  } catch (error) {
    console.error("加载AI配置失败:", error);
    ElMessage.error("加载AI配置失败");
    aiConfigs.value = [];
    currentConfig.value = null;
  } finally {
    loading.value = false;
  }
};

const openCreateDialog = () => {
  isCreating.value = true;
  editingConfig.value = null;
  configForm.value = {
    name: '',
    provider: 'openai',
    api_key: '',
    model_name: 'gpt-3.5-turbo',
    base_url: ''
  };
  showConfigDialog.value = true;
};

const openEditDialog = (config: AIModelConfig) => {
  isCreating.value = false;
  editingConfig.value = config;
  configForm.value = {
    name: config.name,
    provider: config.provider,
    api_key: config.api_key,
    model_name: config.model_name,
    base_url: config.base_url || ''
  };
  showConfigDialog.value = true;
};

const saveConfig = async () => {
  try {
    loading.value = true;
    
    let result;
    if (isCreating.value) {
      result = await apiService.createAIConfig(configForm.value);
    } else if (editingConfig.value) {
      result = await apiService.updateAIConfigById(editingConfig.value.id!, configForm.value);
    }
    
    if (result && result.success) {
      ElMessage.success(result.msg || (isCreating.value ? "配置创建成功" : "配置更新成功"));
      showConfigDialog.value = false;
      await loadAIConfigs();
    } else {
      ElMessage.error(result?.msg || "保存配置失败");
    }
  } catch (error: any) {
    console.error("保存配置失败:", error);
    const errorMsg = error.response?.data?.msg || error.message || "保存配置失败";
    ElMessage.error(errorMsg);
  } finally {
    loading.value = false;
  }
};

const deleteConfig = async (config: AIModelConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${config.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    const result = await apiService.deleteAIConfig(config.id!);
    if (result.success) {
      ElMessage.success(result.msg || "配置删除成功");
      await loadAIConfigs();
    } else {
      ElMessage.error(result.msg || "删除配置失败");
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error("删除配置失败:", error);
      const errorMsg = error.response?.data?.msg || error.message || "删除配置失败";
      ElMessage.error(errorMsg);
    }
  }
};

const setCurrentConfig = async (config: AIModelConfig) => {
  try {
    const result = await apiService.setCurrentAIConfig(config.id!);
    if (result.success) {
      ElMessage.success(result.msg || `已切换到配置 "${config.name}"`);
      await loadAIConfigs();
    } else {
      ElMessage.error(result.msg || "切换配置失败");
    }
  } catch (error: any) {
    console.error("切换配置失败:", error);
    const errorMsg = error.response?.data?.msg || error.message || "切换配置失败";
    ElMessage.error(errorMsg);
  }
};

// 测试AI连接
const testAIConnection = async (config?: AIModelConfig) => {
  try {
    testingConnection.value = true;
    const configToTest = config || testConfig.value;
    
    // 确保配置数据完整
    if (!configToTest.api_key) {
      ElMessage.error("请先配置API密钥");
      return;
    }
    
    const result = await apiService.testAIConnection(configToTest);
    if (result.success) {
      ElMessage.success(result.msg || "AI连接测试成功");
    } else {
      ElMessage.error(result.msg || 'AI连接测试失败');
    }
  } catch (error: any) {
    console.error("测试AI连接失败:", error);
    const errorMsg = error.response?.data?.msg || error.message || "测试AI连接失败";
    ElMessage.error(errorMsg);
  } finally {
    testingConnection.value = false;
  }
};

// 在对话框中测试配置
const testConfigInDialog = async () => {
  try {
    testingConnection.value = true;
    
    // 确保配置数据完整
    if (!configForm.value.api_key) {
      ElMessage.error("请先配置API密钥");
      return;
    }
    
    const result = await apiService.testAIConnection(configForm.value);
    if (result.success) {
      ElMessage.success(result.msg || "AI连接测试成功");
    } else {
      ElMessage.error(result.msg || 'AI连接测试失败');
    }
  } catch (error: any) {
    console.error("测试AI连接失败:", error);
    const errorMsg = error.response?.data?.msg || error.message || "测试AI连接失败";
    ElMessage.error(errorMsg);
  } finally {
    testingConnection.value = false;
  }
};

const resetTestConfig = () => {
  testConfig.value = {
    name: '',
    provider: 'openai',
    api_key: '',
    model_name: 'gpt-3.5-turbo',
    base_url: ''
  };
};

// 加载Whisper模型
const loadWhisperModels = async () => {
  try {
    // 加载Whisper模型
    const whisperResponse = await apiService.getWhisperModels();
    if (whisperResponse.success && whisperResponse.data) {
      whisperModels.value = whisperResponse.data;

      // 优先使用store中的当前模型
      const storeCurrentModel = appStore.currentWhisperModel;
      if (storeCurrentModel) {
        selectedWhisperModel.value = storeCurrentModel;
        // 更新模型列表中的当前状态
        whisperModels.value.forEach((model) => {
          model.is_current = model.name === storeCurrentModel;
        });
      } else {
        // 如果store中没有，使用服务器返回的当前模型
        const current = whisperResponse.data.find((m) => m.is_current);
        if (current) {
          selectedWhisperModel.value = current.name;
          appStore.setCurrentWhisperModel(current.name);
        }
      }

      appStore.setWhisperModels(whisperResponse.data);
    }
  } catch (error: any) {
    ElMessage.error(`加载Whisper模型失败: ${error.message || error}`);
  }
};

// 选择Whisper模型
const selectWhisperModel = async () => {
  try {
    loading.value = true;

    const response = await apiService.selectWhisperModel(selectedWhisperModel.value);
    if (response.success) {
      // 更新本地状态
      whisperModels.value.forEach((model) => {
        model.is_current = model.name === selectedWhisperModel.value;
      });
      appStore.setCurrentWhisperModel(selectedWhisperModel.value);
      ElMessage.success("Whisper模型切换成功！");
    } else {
      throw new Error(response.msg);
    }
  } catch (error: any) {
    ElMessage.error(`模型切换失败: ${error.message || error}`);
  } finally {
    loading.value = false;
  }
};

// 组件挂载时加载配置
onMounted(async () => {
  await loadAIConfigs();
  await loadWhisperModels();
});
</script>

<template>
  <div class="settings-wrapper">
    <el-scrollbar height="100vh">
      <div class="settings-container">
        <!-- AI配置列表管理 -->
        <el-card class="settings-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h3>AI模型配置</h3>
          <el-button type="primary" @click="openCreateDialog"> 新增配置 </el-button>
        </div>
      </template>

      <!-- 当前配置显示 -->
      <div class="current-config" v-if="currentConfig">
        <h4>当前配置</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="配置名称">{{ currentConfig.name }}</el-descriptions-item>
          <el-descriptions-item label="AI提供商">{{ aiProviders.find(p => p.value === currentConfig.provider)?.label }}</el-descriptions-item>
          <el-descriptions-item label="模型名称">{{ currentConfig.model_name }}</el-descriptions-item>
          <el-descriptions-item label="API密钥">{{ currentConfig.api_key ? '已配置' : '未配置' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 配置列表 -->
      <div class="config-list">
        <h4>所有配置</h4>
        <el-table :data="aiConfigs" style="width: 100%">
          <el-table-column prop="name" label="配置名称" />
          <el-table-column prop="provider" label="AI提供商">
            <template #default="{ row }">
              {{ aiProviders.find(p => p.value === row.provider)?.label }}
            </template>
          </el-table-column>
          <el-table-column prop="model_name" label="模型名称" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_current ? 'success' : 'info'">
                {{ row.is_current ? "当前" : "可用" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-space>
                <el-button size="small" @click="testAIConnection(row)" :loading="testingConnection">
                  测试
                </el-button>
                <el-button size="small" type="primary" @click="setCurrentConfig(row)" :disabled="row.is_current">
                  设为当前
                </el-button>
                <el-button size="small" @click="openEditDialog(row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click="deleteConfig(row)" :disabled="row.is_current">
                  删除
                </el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 配置表单对话框 -->
    <el-dialog
      v-model="showConfigDialog"
      :title="isCreating ? '新增配置' : '编辑配置'"
      width="600px"
    >
      <el-form :model="configForm" label-width="120px">
        <el-form-item label="配置名称" required>
          <el-input v-model="configForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        
        <el-form-item label="AI提供商" required>
          <el-select v-model="configForm.provider" placeholder="选择AI提供商" style="width: 100%">
            <el-option
              v-for="provider in aiProviders"
              :key="provider.value"
              :label="provider.label"
              :value="provider.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="API密钥" required>
          <el-input
            v-model="configForm.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password
          />
        </el-form-item>

        <el-form-item label="模型名称" required>
          <el-select
            v-model="configForm.model_name"
            placeholder="选择模型"
            style="width: 100%"
            filterable
            allow-create
          >
            <el-option
              v-for="model in modelOptions[configForm.provider as keyof typeof modelOptions]"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="自定义API地址" v-if="configForm.provider === 'custom'">
          <el-input v-model="configForm.base_url" placeholder="https://api.example.com/v1" />
        </el-form-item>
        
        <!-- 只在新增配置时显示测试连接 -->
        <el-form-item v-if="isCreating">
          <el-button @click="testConfigInDialog" :loading="testingConnection">
            测试连接
          </el-button>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-space>
          <el-button @click="showConfigDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="loading">
            {{ isCreating ? '创建' : '保存' }}
          </el-button>
        </el-space>
      </template>
    </el-dialog>

    <!-- 独立测试连接区域 -->
    <!-- <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <h3>测试AI连接</h3>
          <el-button @click="resetTestConfig">重置</el-button>
        </div>
      </template>

      <el-form :model="testConfig" label-width="120px" class="config-form">
        <el-form-item label="AI提供商">
          <el-select v-model="testConfig.provider" placeholder="选择AI提供商" style="width: 100%">
            <el-option
              v-for="provider in aiProviders"
              :key="provider.value"
              :label="provider.label"
              :value="provider.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="API密钥">
          <el-input
            v-model="testConfig.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password
          />
        </el-form-item>

        <el-form-item label="模型名称">
          <el-select
            v-model="testConfig.model_name"
            placeholder="选择模型"
            style="width: 100%"
            filterable
            allow-create
          >
            <el-option
              v-for="model in modelOptions[testConfig.provider as keyof typeof modelOptions]"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="自定义API地址" v-if="testConfig.provider === 'custom'">
          <el-input v-model="testConfig.base_url" placeholder="https://api.example.com/v1" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="testAIConnection()" :loading="testingConnection">
            测试连接
          </el-button>
        </el-form-item>
      </el-form>
    </el-card> -->

    <el-card class="settings-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <h3>Whisper模型配置</h3>
        </div>
      </template>

      <div class="whisper-config">
        <el-form label-width="120px">
          <el-form-item label="当前模型">
            <el-select
              v-model="selectedWhisperModel"
              placeholder="选择Whisper模型"
              style="width: 100%"
              @change="selectWhisperModel"
            >
              <el-option
                v-for="model in whisperModels"
                :key="model.name"
                :label="`${model.name} (${model.size})`"
                :value="model.name"
              >
                <span>{{ model.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">
                  {{ model.size }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>

        <div class="model-info" v-if="whisperModels.length > 0">
          <h4>可用模型列表</h4>
          <el-table :data="whisperModels" style="width: 100%">
            <el-table-column prop="name" label="模型名称" />
            <el-table-column prop="size" label="大小" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_current ? 'success' : 'info'">
                  {{ row.is_current ? "当前" : "可用" }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <h3>使用说明</h3>
        </div>
      </template>

      <div class="help-content">
        <h4>AI模型配置说明</h4>
        <ul>
          <li><strong>OpenAI:</strong> 需要OpenAI API密钥，支持GPT系列模型</li>
          <li><strong>Anthropic:</strong> 需要Anthropic API密钥，支持Claude系列模型</li>
          <li><strong>Google:</strong> 需要Google AI API密钥，支持Gemini系列模型</li>
          <li><strong>自定义:</strong> 支持兼容OpenAI API格式的自定义服务</li>
        </ul>

        <h4>Whisper模型说明</h4>
        <ul>
          <li><strong>tiny:</strong> 最快速度，较低准确率，适合快速测试</li>
          <li><strong>base:</strong> 平衡速度和准确率</li>
          <li><strong>small:</strong> 较好准确率，适中速度</li>
          <li><strong>medium:</strong> 高准确率，较慢速度</li>
          <li><strong>large:</strong> 最高准确率，最慢速度</li>
        </ul>
        </div>
      </el-card>
      </div>
    </el-scrollbar>
  </div>
</template>

<style lang="scss" scoped>
.settings-wrapper {
  height: 100%;
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #e2e8f0;
  font-weight: 600;
}

.config-form {
  max-width: 600px;
}

.whisper-config {
  max-width: 600px;
}

.model-info {
  margin-top: 24px;
}

.model-info h4 {
  margin-bottom: 16px;
  color: #e2e8f0;
  font-weight: 600;
}

.help-content h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #e2e8f0;
  font-weight: 600;
}

.help-content ul {
  margin: 0;
  padding-left: 20px;
}

.help-content li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.help-content strong {
  color: #00d4ff;
}

.current-config {
  margin-bottom: 24px;
}

.current-config h4 {
  margin-bottom: 16px;
  color: #e2e8f0;
  font-weight: 600;
}

.config-list {
  margin-top: 24px;
}

.config-list h4 {
  margin-bottom: 16px;
  color: #e2e8f0;
  font-weight: 600;
}

.el-descriptions {
  margin-bottom: 16px;
}

.el-table {
  margin-top: 16px;
}
</style>
