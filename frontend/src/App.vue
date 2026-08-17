<template>
  <div class="app-shell">
    <!-- 左侧统一导航栏 -->
    <aside class="sidebar" :class="{ collapsed: store.isSidebarCollapsed }">
      <div class="side-brand">
        <div class="brand-logo"><Reading /></div>
        <span class="brand-text">公考行测知识库</span>
      </div>

      <nav class="side-nav">
        <router-link v-for="item in menuItems" :key="item.path" :to="item.path"
                     class="nav-item" active-class="active" :title="item.label">
          <el-icon class="nav-ico"><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- 右主区 -->
    <div class="main-col">
      <!-- 顶栏 -->
      <header class="topbar">
        <button class="icon-btn" @click="store.toggleSidebar()" :title="store.isSidebarCollapsed ? '展开侧栏' : '收起侧栏'">
          <el-icon><Fold v-if="!store.isSidebarCollapsed" /><Expand v-else /></el-icon>
        </button>

        <div class="top-search">
          <el-icon class="search-ico"><Search /></el-icon>
          <input v-model="searchKw" @keyup.enter="doSearch" placeholder="搜索题目、知识点…" />
        </div>

        <div class="top-spacer"></div>

        <div v-if="nearestExam" class="top-countdown" :title="nearestExam.name">
          <el-icon><Timer /></el-icon>
          <span class="cd-num">{{ nearestExam.days_left }}<i>天</i></span>
          <span class="cd-type">{{ nearestExam.exam_type }}</span>
        </div>

        <button class="icon-btn" @click="store.toggleDarkMode()" :title="darkMode ? '切换浅色' : '切换深色'">
          <el-icon><Moon v-if="darkMode" /><Sunny v-else /></el-icon>
        </button>
      </header>

      <!-- 内容 -->
      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from './stores/app'

const store = useAppStore()
const route = useRoute()
const router = useRouter()

const menuItems = [
  { path: '/dashboard', icon: 'DataLine', label: '首页看板' },
  { path: '/question-input', icon: 'EditPen', label: '题目录入' },
  { path: '/deposit', icon: 'Upload', label: '核对并入库' },
  { path: '/question-list', icon: 'Collection', label: '题库列表' },
  { path: '/knowledge', icon: 'Reading', label: '行测知识库' },
  { path: '/solve-library', icon: 'Lightning', label: '行测解题库' },
  { path: '/errors', icon: 'Warning', label: '错题集' },
  { path: '/review', icon: 'Refresh', label: '智能复习' },
  { path: '/notes', icon: 'Notebook', label: '笔记管理' },
  { path: '/visualization', icon: 'TrendCharts', label: '可视化大屏' },
  { path: '/countdown', icon: 'Timer', label: '考试倒计时' },
  { path: '/prompts', icon: 'Document', label: '提示词管理' },
  { path: '/stages', icon: 'Calendar', label: '备考阶段' },
  { path: '/backup', icon: 'Files', label: '备份导出' },
]

const searchKw = ref('')
const darkMode = computed(() => store.darkMode)
const nearestExam = computed(() => {
  const active = store.examCountdowns.filter(e => !e.is_passed && e.days_left >= 0)
  return active.length > 0 ? active[0] : null
})

function doSearch() {
  if (!searchKw.value.trim()) return
  router.push({ path: '/question-list', query: { keyword: searchKw.value.trim() } })
}

onMounted(() => {
  store.initTheme()
  store.loadCategories()
  store.loadExamCountdowns()
})
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧栏 */
.sidebar {
  width: 248px;
  flex-shrink: 0;
  background: var(--bg-elevated);
  border-right: 1px solid var(--border-base);
  display: flex;
  flex-direction: column;
  transition: width 0.22s ease;
  overflow: hidden;
}
.sidebar.collapsed { width: 64px; }

.side-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
  overflow: hidden;
  white-space: nowrap;
}
.brand-logo {
  width: 32px; height: 32px; flex-shrink: 0;
  border-radius: 9px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
}
.brand-text {
  font-size: 15px; font-weight: 800;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.side-nav { padding: 10px 10px 4px; display: flex; flex-direction: column; gap: 2px; flex-shrink: 0; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 12px; border-radius: var(--radius-md);
  text-decoration: none; color: var(--text-secondary);
  font-size: 13.5px; transition: all 0.15s; white-space: nowrap; overflow: hidden;
}
.nav-item:hover { background: var(--bg-subtle); color: var(--text-primary); }
.nav-item.active {
  background: var(--primary-bg); color: var(--primary); font-weight: 600;
}
.nav-ico { font-size: 17px; flex-shrink: 0; }

/* 折叠态：只显示图标 */
.sidebar.collapsed .brand-text,
.sidebar.collapsed .nav-label { display: none; }
.sidebar.collapsed .side-brand { justify-content: center; padding: 16px 0; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 9px 0; }

/* 主区 */
.main-col { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.topbar {
  height: 56px; flex-shrink: 0;
  display: flex; align-items: center; gap: 12px;
  padding: 0 16px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-base);
  z-index: 20;
}
.top-search {
  display: flex; align-items: center; gap: 7px;
  background: var(--bg-subtle); border: 1px solid var(--border-base);
  border-radius: 999px; padding: 6px 14px; width: 320px; max-width: 40vw;
  transition: border-color 0.15s;
}
.top-search:focus-within { border-color: var(--primary); }
.search-ico { font-size: 14px; opacity: 0.55; flex-shrink: 0; }
.top-search input {
  border: none; background: transparent; outline: none;
  font-size: 13px; color: var(--text-primary); width: 100%;
}
.top-spacer { flex: 1; }
.top-countdown {
  display: flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff; padding: 6px 14px; border-radius: 999px; font-size: 12px; flex-shrink: 0;
}
.top-countdown .el-icon { font-size: 14px; }
.cd-num { font-weight: 800; font-size: 15px; }
.cd-num i { font-size: 10px; font-weight: 400; margin-left: 1px; font-style: normal; }
.cd-type { opacity: 0.9; }
.icon-btn {
  background: none; border: none; font-size: 17px; cursor: pointer;
  padding: 7px 9px; border-radius: var(--radius-sm); transition: background 0.2s;
  color: var(--text-secondary); display: flex; align-items: center;
}
.icon-btn:hover { background: var(--bg-subtle); color: var(--text-primary); }

.content { flex: 1; overflow-y: auto; padding: 22px; background: var(--bg-base); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.18s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* 响应式 */
@media (max-width: 768px) {
  .sidebar { position: absolute; z-index: 50; height: 100%; box-shadow: var(--shadow-xl); }
  .top-search { width: 160px; }
}
</style>
