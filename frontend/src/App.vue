<script setup lang="ts">
import { RouterView, useRoute } from "vue-router";
import { ref, computed } from "vue";
import { useAppStore } from "./stores/app";

const route = useRoute();
const appStore = useAppStore();

const activeIndex = computed(() => {
  const path = route.path;
  if (path.startsWith("/notes")) return "1";
  if (path.startsWith("/settings")) return "2";
  if (path.startsWith("/history")) return "3";
  return "1";
});

const menuItems = [
  { index: "1", title: "笔记生成", route: "/notes", icon: "Document" },
  { index: "2", title: "设置", route: "/settings", icon: "Setting" },
  { index: "3", title: "历史记录", route: "/history", icon: "Clock" },
];
</script>

<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo-section">
        <h2>AI笔记生成器</h2>
      </div>
      <el-menu
        :default-active="activeIndex"
        class="sidebar-menu"
        router
        background-color="transparent"
        text-color="#b0c4de"
        active-text-color="#00d4ff"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.index"
          :index="item.route"
          class="menu-item"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-content">
          <h3>{{ route.meta?.title || "音视频AI笔记生成" }}</h3>
          <div class="header-actions">
            <el-badge :is-dot="appStore.loading" type="warning">
              <el-button v-if="appStore.loading" type="info" size="small" loading disabled>
                处理中...
              </el-button>
            </el-badge>
          </div>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="content">
        <RouterView />
      </el-main>
    </el-container>
  </div>
</template>

<style lang="scss" scoped>
@import "@/assets/variables.scss";
@import "@/assets/mixins.scss";

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: $gradient-dark;
}

.sidebar {
  @include glass-card;
  border-radius: 0;
  background: $background-glass;
  color: $text-primary;
  box-shadow: $shadow-md;
  border-right: 1px solid rgba(0, 212, 255, 0.2);
}

.logo-section {
  padding: $spacing-xl;
  text-align: center;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  // background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.1));

  h2 {
    margin: 0;
    font-size: $font-size-lg;
    font-weight: $font-weight-semibold;
    color: $text-accent;
    @include tech-glow($primary-color);
    // text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    box-shadow: unset !important;
  }
}

.sidebar-menu {
  border: none;
}

.menu-item {
  @include menu-item-style;
}

.main-container {
  flex: 1;
  background: $background-light;
}

.header {
  @include glass-card;
  border-radius: 0;
  background: $background-glass;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  box-shadow: $shadow-sm;
  padding: 0 $spacing-xxl;
  backdrop-filter: blur(10px);
}

.header-content {
  @include flex-between;
  height: 100%;

  h3 {
    margin: 0;
    color: $text-primary;
    font-weight: $font-weight-semibold;
    text-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
  }
}

.content {
  padding: 0;
  height: calc(100% - 60px);
  overflow: hidden;
}

/* AI科技风菜单样式 */
:deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  border-radius: $border-radius-md;
  margin: $spacing-xs;
  transition: all 0.3s ease;
}

:deep(.el-menu-item.is-active) {
  background: $gradient-secondary !important;
  @include tech-glow($primary-color);
  transform: translateX(5px);
}

:deep(.el-menu-item:hover) {
  background: rgba(0, 212, 255, 0.1) !important;
  transform: translateX(3px);
  @include tech-glow($primary-color);
}
</style>
