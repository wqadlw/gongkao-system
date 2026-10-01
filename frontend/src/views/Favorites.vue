<template>
  <div class="fav-page">
    <div class="page-header">
      <div>
        <h2><el-icon><StarFilled /></el-icon> 我的收藏</h2>
        <p class="sub">跨题目 · 资料 · 知识点 · 解题技巧的统一收藏夹</p>
      </div>
    </div>

    <!-- 类型 tabs -->
    <div class="fav-tabs">
      <button
        v-for="t in TABS" :key="t.type"
        class="fav-tab" :class="{ active: currentType === t.type }"
        @click="switchType(t.type)"
      >
        <el-icon><component :is="t.icon" /></el-icon> {{ t.label }}
        <i>{{ counts[t.type] || 0 }}</i>
      </button>
    </div>

    <div v-loading="loading" class="fav-list">
      <div v-for="it in items" :key="it.favorite_id" class="card fav-card" @click="go(it)">
        <div class="fav-main">
          <div class="fav-title-row">
            <span class="fav-badge">{{ it.badge || currentTypeLabel }}</span>
            <span class="fav-title">{{ it.title }}</span>
          </div>
          <div v-if="it.subtitle" class="fav-sub">{{ it.subtitle }}</div>
          <div
            v-if="it.note" class="fav-note"
            title="点击编辑备注" @click.stop="editNote(it)"
          ><el-icon><ChatLineSquare /></el-icon> {{ it.note }}</div>
          <div
            v-else class="fav-note add" title="添加备注" @click.stop="editNote(it)"
          ><el-icon><ChatLineSquare /></el-icon> 添加备注</div>
          <div class="fav-time">收藏于 {{ it.collect_time }}</div>
        </div>
        <button class="fav-remove" title="取消收藏" @click.stop="removeFavorite(it)">
          <el-icon><StarFilled /></el-icon>
        </button>
      </div>
      <div v-if="!loading && items.length === 0" class="fav-empty">
        <el-icon class="empty-icon"><Star /></el-icon>
        <div class="empty-text">还没有收藏任何{{ currentTypeLabel }}</div>
        <div class="empty-sub">在各页面的星标处点击即可收藏；收藏支持跨模块汇总在这里</div>
      </div>
    </div>

    <el-pagination
      v-if="total > pageSize" layout="prev, pager, next"
      :total="total" :page-size="pageSize" :current-page="page"
      @current-change="p => { page = p; loadList() }"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { favoritesApi } from '../api'

const router = useRouter()

const TABS = [
  { type: 'question', label: '题目', icon: 'EditPen' },
  { type: 'resource', label: '资料', icon: 'FolderOpened' },
  { type: 'knowledge', label: '知识点', icon: 'Reading' },
  { type: 'solve_item', label: '解题技巧', icon: 'Lightning' },
]

const currentType = ref('question')
const items = ref([])
const counts = ref({})
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

const currentTypeLabel = computed(() => TABS.find(t => t.type === currentType.value)?.label || '')

async function loadList() {
  loading.value = true
  try {
    const res = await favoritesApi.list({ obj_type: currentType.value, page: page.value, page_size: pageSize })
    items.value = res.data.items
    total.value = res.data.total
    counts.value = res.data.counts || {}
  } catch { ElMessage.error('收藏列表加载失败') }
  finally { loading.value = false }
}

function switchType(t) {
  currentType.value = t
  page.value = 1
  loadList()
}

async function editNote(it) {
  try {
    const { value } = await ElMessageBox.prompt('给这条收藏写个备注（为什么收藏/复习提示）：', '收藏备注', {
      inputValue: it.note || '', inputPlaceholder: '例如：错因是量级换算，考前必看',
      confirmButtonText: '保存', cancelButtonText: '取消',
    })
    await favoritesApi.updateNote({ obj_type: currentType.value, obj_id: it.obj_id, note: value || '' })
    it.note = value || ''
    ElMessage.success('备注已保存')
  } catch (e) {
    if (e !== 'cancel' && e?.message !== 'cancel') { /* 用户取消不提示 */ }
  }
}

async function removeFavorite(it) {
  const ok = await ElMessageBox.confirm('取消收藏该项？', '确认', { type: 'warning' }).catch(() => false)
  if (!ok) return
  try {
    await favoritesApi.toggle({ obj_type: currentType.value, obj_id: it.obj_id })
    ElMessage.success('已取消收藏')
    loadList()
  } catch { ElMessage.error('操作失败') }
}

function go(it) {
  if (it.route) router.push(it.route)
}

onMounted(loadList)
</script>

<style scoped>
.fav-page { max-width: 960px; margin: 0 auto; }
.page-header h2 { margin: 0; display: flex; align-items: center; gap: 8px; color: var(--warning); }
.page-header .sub { margin: 4px 0 0; font-size: 12.5px; color: var(--text-tertiary); }

.fav-tabs { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.fav-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 18px; border: 1px solid var(--border-base); border-radius: 999px;
  background: var(--bg-elevated); font-size: 13.5px; color: var(--text-secondary); cursor: pointer;
  transition: all 0.15s;
}
.fav-tab i { font-style: normal; font-size: 11px; color: var(--text-tertiary); }
.fav-tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }
.fav-tab.active i { color: rgba(255,255,255,0.8); }

.fav-list { display: flex; flex-direction: column; gap: 10px; min-height: 160px; }
.fav-card {
  display: flex; align-items: center; gap: 12px; padding: 14px 18px;
  cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
}
.fav-card:hover { transform: translateX(3px); box-shadow: var(--shadow-md); }
.fav-main { flex: 1; min-width: 0; }
.fav-title-row { display: flex; align-items: center; gap: 8px; min-width: 0; }
.fav-badge {
  flex-shrink: 0; font-size: 11px; padding: 2px 10px; border-radius: 999px;
  background: var(--primary-bg); color: var(--primary); font-weight: 600;
}
.fav-title { font-size: 14px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fav-sub { font-size: 12px; color: var(--text-tertiary); margin-top: 3px; }
.fav-note { font-size: 12.5px; color: var(--text-secondary); margin-top: 5px; display: flex; align-items: center; gap: 4px; cursor: pointer; }
.fav-note:hover { color: var(--primary); }
.fav-note.add { color: var(--text-tertiary); font-style: italic; }
.fav-time { font-size: 11.5px; color: var(--text-tertiary); margin-top: 4px; }
.fav-remove {
  flex-shrink: 0; border: none; background: none; cursor: pointer;
  color: var(--warning); font-size: 18px; padding: 8px; border-radius: 50%;
  transition: all 0.15s; display: flex;
}
.fav-remove:hover { background: var(--warning-bg); transform: scale(1.15); }

.fav-empty { text-align: center; padding: 50px 20px; color: var(--text-tertiary); }
.empty-icon { font-size: 52px; }
.empty-text { font-size: 16px; font-weight: 600; color: var(--text-secondary); margin-top: 10px; }
.empty-sub { font-size: 13px; margin-top: 6px; }
</style>
