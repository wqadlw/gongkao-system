<template>
  <div class="errors-page">
    <div class="page-header">
      <h2>⚠️ 错题集</h2>
      <button class="btn-primary" @click="$router.push('/review?mode=error')">🔄 错题重做</button>
    </div>

    <div class="stat-grid">
      <div class="stat-card danger"><div class="stat-num">{{ stats.total || 0 }}</div><div class="stat-label">错题总数</div></div>
      <div class="stat-card warning"><div class="stat-num">{{ stats.overdue || 0 }}</div><div class="stat-label">逾期未复习</div></div>
      <div class="stat-card info"><div class="stat-num">{{ stats.weak || 0 }}</div><div class="stat-label">薄弱错题</div></div>
      <div class="stat-card success"><div class="stat-num">{{ stats.mastered || 0 }}</div><div class="stat-label">已攻克</div></div>
    </div>

    <div class="filter-bar">
      <select v-model="filters.level1" @change="loadList" class="filter-select">
        <option value="">全部模块</option>
        <option v-for="m in modules" :key="m" :value="m">{{ m }}</option>
      </select>
      <select v-model="filters.type" @change="loadList" class="filter-select">
        <option value="">全部错题</option>
        <option value="overdue">逾期未复习</option>
        <option value="weak">薄弱(≤2星)</option>
      </select>
    </div>

    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th width="60">ID</th>
            <th width="100">模块</th>
            <th>题干/考点</th>
            <th width="80">掌握度</th>
            <th width="120">下次复习</th>
            <th width="100">状态</th>
            <th width="80">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in questions" :key="q.id" @click="$router.push(`/question/${q.id}`)" class="clickable">
            <td>{{ q.id }}</td>
            <td><span class="tag" :class="q.level1">{{ q.level1 }}</span></td>
            <td>
              <div class="q-text">{{ q.question_raw?.slice(0, 60) }}...</div>
              <div class="q-cat">{{ q.level3 }}{{ q.level4 ? ' / ' + q.level4 : '' }}</div>
            </td>
            <td><div class="stars">{{ '★'.repeat(q.master_level) }}{{ '☆'.repeat(5 - q.master_level) }}</div></td>
            <td class="time-cell">{{ q.next_review_time }}</td>
            <td>
              <span v-if="isOverdue(q)" class="status-tag overdue">逾期</span>
              <span v-else class="status-tag normal">正常</span>
            </td>
            <td @click.stop><button class="btn-icon" @click="$router.push(`/question/${q.id}`)">👁️</button></td>
          </tr>
          <tr v-if="questions.length === 0"><td colspan="7" class="empty">暂无错题</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { questionApi } from '../api'

const questions = ref([])
const stats = ref({ total: 0, overdue: 0, weak: 0, mastered: 0 })
const modules = ['政治理论', '常识判断', '言语理解与表达', '数量关系', '判断推理', '资料分析']
const filters = reactive({ level1: '', type: '' })

function isOverdue(q) {
  if (!q.next_review_time) return false
  return new Date(q.next_review_time) < new Date()
}

async function loadList() {
  const params = { page: 1, page_size: 100, is_error: true }
  if (filters.level1) params.level1 = filters.level1
  const res = await questionApi.getList(params)
  let items = res.data.items
  if (filters.type === 'overdue') items = items.filter(q => isOverdue(q))
  else if (filters.type === 'weak') items = items.filter(q => q.master_level <= 2)
  questions.value = items

  stats.value = {
    total: res.data.total,
    overdue: res.data.items.filter(q => isOverdue(q)).length,
    weak: res.data.items.filter(q => q.master_level <= 2).length,
    mastered: res.data.items.filter(q => q.master_level >= 4).length,
  }
}

onMounted(loadList)
</script>

<style scoped>
.errors-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: var(--bg-elevated); padding: 20px; border-radius: var(--radius-lg); text-align: center; border: 1px solid var(--border-light); }
.stat-num { font-size: 32px; font-weight: 800; }
.stat-card.danger .stat-num { color: var(--danger); }
.stat-card.warning .stat-num { color: var(--warning); }
.stat-card.info .stat-num { color: var(--info); }
.stat-card.success .stat-num { color: var(--success); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.filter-select { padding: 6px 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 13px; background: var(--bg-elevated); color: var(--text-primary); }
.table-card { background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: var(--bg-subtle); padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.data-table td { padding: 12px 16px; border-bottom: 1px solid var(--border-light); font-size: 13px; }
.data-table tr.clickable { cursor: pointer; }
.data-table tr.clickable:hover { background: var(--bg-hover); }
.q-text { font-size: 13px; margin-bottom: 2px; }
.q-cat { font-size: 11px; color: var(--text-tertiary); }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.tag.政治理论 { background: var(--danger-bg); color: var(--danger); }
.tag.常识判断 { background: var(--warning-bg); color: var(--warning); }
.tag.言语理解与表达 { background: var(--primary-bg); color: var(--primary); }
.tag.数量关系 { background: var(--success-bg); color: var(--success); }
.tag.判断推理 { background: var(--info-bg); color: var(--info); }
.tag.资料分析 { background: #fce7f3; color: #db2777; }
.stars { color: var(--warning); font-size: 12px; }
.time-cell { font-size: 12px; color: var(--text-tertiary); }
.status-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.status-tag.overdue { background: var(--danger-bg); color: var(--danger); }
.status-tag.normal { background: var(--success-bg); color: var(--success); }
.empty { text-align: center; color: var(--text-tertiary); padding: 40px; }
.btn-primary { background: var(--primary); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-icon { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; }
</style>
