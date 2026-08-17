<template>
  <div class="notes-page">
    <div class="page-header">
      <div>
        <h2>📓 笔记管理</h2>
        <p class="sub">按模块筛选、检索与管理你的备考笔记</p>
      </div>
      <button class="btn-default" @click="exportNotes">📥 导出全部</button>
    </div>

    <div class="filter-bar">
      <div class="select-wrap">
        <select v-model="moduleFilter" @change="loadList" class="module-select">
          <option value="">全部模块</option>
          <option v-for="m in modules" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
      <input v-model="keyword" placeholder="搜索笔记内容…" class="search-input" @keyup.enter="loadList" @blur="loadList" />
      <label class="checkbox-label"><input type="checkbox" v-model="onlyCollect" @change="loadList" /> 仅看收藏</label>
      <span class="count">共 {{ notes.length }} 条</span>
    </div>

    <div class="notes-grid">
      <div v-for="note in notes" :key="note.id" class="note-card" @click="openDetail(note)">
        <div class="note-head">
          <span class="mod-tag" :style="modStyle(note.level1)">{{ note.level1 || '未分类' }}</span>
          <h3 class="note-title">{{ cardTitle(note) }}</h3>
          <div class="note-actions" @click.stop>
            <button class="btn-icon" :class="{ active: note.is_collect }" @click="toggleCollect(note)" title="收藏">★</button>
            <button class="btn-icon" @click="editNote(note)" title="编辑">✏️</button>
            <button class="btn-icon danger" @click="deleteNote(note)" title="删除">🗑️</button>
          </div>
        </div>
        <div class="note-body">
          <div v-if="cardTags(note).length" class="note-tags">
            <span v-for="t in cardTags(note)" :key="t" class="note-tagchip">{{ t }}</span>
          </div>
          <div v-if="note.question_display" class="note-q md-body" v-html="md(note.question_display)"></div>
          <p v-if="cardSummary(note)" class="note-summary">{{ cardSummary(note) }}</p>
          <div v-if="note.type_judgment" class="note-judge"><span class="nl">题型判定</span><span class="nv md-body md-inline" v-html="mdi(note.type_judgment)"></span></div>
        </div>
        <div class="note-foot">
          <span class="note-time">{{ note.create_time }}</span>
          <div class="note-foot-actions" @click.stop>
            <button v-if="note.question_id" class="foot-link" @click="goQuestion(note.question_id)">来源题目 ›</button>
            <span class="detail-link">详情 ›</span>
          </div>
        </div>
      </div>
      <div v-if="notes.length === 0" class="empty">暂无笔记，在题目详情页点击「✨ 一键生成笔记」即可生成</div>
    </div>

    <!-- 详情抽屉 -->
    <div v-if="detailVisible && active" class="drawer-overlay" @click="detailVisible = false">
      <div class="drawer" @click.stop>
        <div class="drawer-head">
          <div class="drawer-title">
            <span class="mod-tag" :style="modStyle(active.level1)">{{ active.level1 }}</span>
            <b>{{ cardTitle(active) }}</b>
          </div>
          <button class="btn-icon" @click="detailVisible = false">✕</button>
        </div>
        <div class="drawer-body">
          <div v-if="cardSummary(active) || cardTags(active).length" class="d-cardinfo">
            <p v-if="cardSummary(active)" class="d-summary">{{ cardSummary(active) }}</p>
            <div v-if="cardTags(active).length" class="d-tags">
              <span v-for="t in cardTags(active)" :key="t" class="d-tagchip">{{ t }}</span>
            </div>
          </div>
          <div v-if="active.question_display" class="d-sec">
            <div class="d-label">题目</div>
            <div class="md-body" v-html="md(active.question_display)"></div>
          </div>
          <div v-if="active.type_judgment" class="d-sec"><div class="d-label">题型判定</div><div class="md-body" v-html="md(active.type_judgment)"></div></div>
          <div v-if="active.knowledge_points" class="d-sec"><div class="d-label">知识点</div><div class="md-body" v-html="md(active.knowledge_points)"></div></div>
          <div v-if="active.logic_chain" class="d-sec"><div class="d-label">解题逻辑链</div><div class="md-body" v-html="md(active.logic_chain)"></div></div>
          <div v-if="active.solve_steps" class="d-sec"><div class="d-label">解题步骤</div><div class="md-body" v-html="md(active.solve_steps)"></div></div>
          <div v-if="active.pitfalls" class="d-sec warn"><div class="d-label">避坑要点</div><div class="md-body" v-html="md(active.pitfalls)"></div></div>
          <div v-if="active.speed_tips" class="d-sec tip"><div class="d-label">提速技巧</div><div class="md-body" v-html="md(active.speed_tips)"></div></div>
          <div v-if="active.question_id" class="d-link">
            <button class="btn-primary" @click="goQuestion(active.question_id)">查看原题 →</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗（带实时预览） -->
    <div v-if="editVisible" class="modal-overlay" @click="editVisible = false">
      <div class="modal wide" @click.stop>
        <div class="modal-header"><h3>编辑笔记</h3><button class="btn-icon" @click="editVisible = false">✕</button></div>
        <div class="modal-body edit-body">
          <div class="edit-form">
            <div class="form-group" v-for="field in editFields" :key="field.key">
              <label>{{ field.label }}</label>
              <textarea v-model="editForm[field.key]" :rows="field.rows || 3"
                @input="editDirty = true"></textarea>
            </div>
          </div>
          <div class="edit-preview">
            <div class="np-title">实时预览</div>
            <div class="np-scroll">
              <div v-if="editForm.card_title || editForm.card_summary || (editForm.card_tags && cardTags(editForm).length)" class="d-cardinfo">
                <p v-if="editForm.card_summary" class="d-summary">{{ editForm.card_summary }}</p>
                <div v-if="editForm.card_tags && cardTags(editForm).length" class="d-tags">
                  <span v-for="t in cardTags(editForm)" :key="t" class="d-tagchip">{{ t }}</span>
                </div>
              </div>
              <div v-if="editForm.question_display" class="d-sec"><div class="d-label">题目</div><div class="md-body" v-html="md(editForm.question_display)"></div></div>
              <div v-if="editForm.type_judgment" class="d-sec"><div class="d-label">题型判定</div><div class="md-body" v-html="md(editForm.type_judgment)"></div></div>
              <div v-if="editForm.knowledge_points" class="d-sec"><div class="d-label">知识点</div><div class="md-body" v-html="md(editForm.knowledge_points)"></div></div>
              <div v-if="editForm.logic_chain" class="d-sec"><div class="d-label">解题逻辑链</div><div class="md-body" v-html="md(editForm.logic_chain)"></div></div>
              <div v-if="editForm.solve_steps" class="d-sec"><div class="d-label">解题步骤</div><div class="md-body" v-html="md(editForm.solve_steps)"></div></div>
              <div v-if="editForm.pitfalls" class="d-sec warn"><div class="d-label">避坑要点</div><div class="md-body" v-html="md(editForm.pitfalls)"></div></div>
              <div v-if="editForm.speed_tips" class="d-sec tip"><div class="d-label">提速技巧</div><div class="md-body" v-html="md(editForm.speed_tips)"></div></div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-default" @click="editVisible = false">取消</button>
          <button class="btn-primary" @click="saveNote">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { noteApi, backupApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { renderMarkdown, renderInline } from '../utils/md'
import { MODULES, modStyle } from '../utils/constants'

const md = renderMarkdown
const mdi = renderInline
const router = useRouter()

const modules = MODULES

const notes = ref([])
const moduleFilter = ref('')
const keyword = ref('')
const onlyCollect = ref(false)
const detailVisible = ref(false)
const active = ref(null)
const editVisible = ref(false)
const editForm = ref({})
const editDirty = ref(false)

const editFields = [
  { key: 'card_title', label: '卡片标题（≤18字）', rows: 1 },
  { key: 'card_tags', label: '考点标签（｜分隔）', rows: 1 },
  { key: 'card_summary', label: '卡片摘要（≤70字）', rows: 2 },
  { key: 'question_display', label: '题目', rows: 4 },
  { key: 'type_judgment', label: '题型判定', rows: 2 },
  { key: 'knowledge_points', label: '知识点', rows: 2 },
  { key: 'logic_chain', label: '解题逻辑链', rows: 3 },
  { key: 'solve_steps', label: '解题步骤', rows: 4 },
  { key: 'pitfalls', label: '避坑要点', rows: 3 },
  { key: 'speed_tips', label: '提速技巧', rows: 3 },
]

async function loadList() {
  const params = {}
  if (moduleFilter.value) params.level1 = moduleFilter.value
  if (keyword.value) params.keyword = keyword.value
  if (onlyCollect.value) params.is_collect = true
  const res = await noteApi.getList(params)
  notes.value = res.data
}

function openDetail(note) {
  active.value = note
  detailVisible.value = true
}
function goQuestion(id) {
  detailVisible.value = false
  router.push('/question/' + id)
}

// 笔记卡片展示完整题目（题干+选项），滚动查看，无需再剥离题干

// 卡片缩略信息（与知识库/解题库卡片一致，缺省时回退）
function cardTitle(note) {
  return (note.card_title || note.level5 || '备考笔记').trim()
}
function cardTags(note) {
  if (!note.card_tags) return []
  return note.card_tags.split(/[｜|/、,，]/).map(s => s.trim()).filter(Boolean)
}
function cardSummary(note) {
  if (note.card_summary) return note.card_summary.trim()
  const fb = (note.knowledge_points || note.solve_steps || '').replace(/[#*`>\n]/g, ' ').trim()
  return fb.slice(0, 70)
}

function editNote(note) {
  editForm.value = { ...note }
  editDirty.value = false
  editVisible.value = true
}

async function saveNote() {
  await noteApi.update(editForm.value.id, editForm.value)
  ElMessage.success('保存成功')
  editVisible.value = false
  loadList()
}

async function toggleCollect(note) {
  await noteApi.update(note.id, { is_collect: !note.is_collect })
  loadList()
}

async function deleteNote(note) {
  await ElMessageBox.confirm('确定删除此笔记？', '提示', { type: 'warning' })
  await noteApi.delete(note.id)
  ElMessage.success('删除成功')
  loadList()
}

async function exportNotes() {
  try {
    const res = await backupApi.exportNotes()
    const url = URL.createObjectURL(new Blob([res.data], { type: 'text/markdown' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `notes_${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

onMounted(loadList)
</script>

<style scoped>
.notes-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 18px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.page-header .sub { margin: 4px 0 0; font-size: 13px; color: var(--text-tertiary); }

.filter-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.select-wrap { position: relative; }
.module-select {
  padding: 8px 32px 8px 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md);
  font-size: 13px; background: var(--bg-elevated); color: var(--text-primary); cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%2394a3b8'/></svg>");
  background-repeat: no-repeat; background-position: right 12px center;
}
.module-select:focus { outline: none; border-color: var(--primary); }
.search-input { padding: 8px 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 13px; background: var(--bg-elevated); color: var(--text-primary); width: 260px; }
.search-input:focus { outline: none; border-color: var(--primary); }
.checkbox-label { font-size: 13px; display: flex; align-items: center; gap: 4px; cursor: pointer; }
.count { font-size: 12px; color: var(--text-tertiary); margin-left: auto; }

.notes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }
.note-card {
  background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light);
  overflow: hidden; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; display: flex; flex-direction: column;
}
.note-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.note-head { padding: 12px 16px; border-bottom: 1px solid var(--border-light); display: flex; align-items: center; gap: 8px; }
.mod-tag { font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 999px; border: 1px solid transparent; flex-shrink: 0; }
.note-title { font-size: 15px; font-weight: 600; margin: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-primary); }
.note-actions { display: flex; gap: 2px; }
.btn-icon { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; }
.btn-icon.active { background: var(--warning); color: #fff; }
.btn-icon.danger:hover { background: var(--danger-bg); }
.note-body { padding: 14px 16px; flex: 1; }
.note-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.note-tagchip { font-size: 11px; padding: 2px 9px; border-radius: 999px; background: var(--primary-soft, rgba(99,102,241,0.1)); color: var(--primary); font-weight: 600; cursor: default; }
.note-q { margin-bottom: 10px; font-size: 12px; line-height: 1.6; color: var(--text-secondary); background: var(--bg-subtle); padding: 8px 10px; border-radius: var(--radius-md); max-height: 180px; overflow-y: auto; }
.note-q :deep(p) { margin: 0 0 6px; }
.note-q :deep(p:last-child) { margin-bottom: 0; }
.note-q :deep(strong) { color: var(--text-primary); font-weight: 500; }
.note-q :deep(ol), .note-q :deep(ul) { padding-left: 18px; margin: 0 0 6px; }
.note-q :deep(li) { margin-bottom: 2px; }
.note-q :deep(code) { background: var(--bg-elevated); padding: 1px 5px; border-radius: 4px; font-size: 11px; }
.note-code { font-size: 11px; background: var(--bg-subtle); padding: 8px 10px; border-radius: var(--radius-md); white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; max-height: 90px; overflow: hidden; margin: 0; color: var(--text-secondary); }
.note-summary { font-size: 13px; line-height: 1.65; color: var(--text-secondary); margin: 0 0 10px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.note-judge { display: flex; gap: 8px; font-size: 12px; line-height: 1.5; }
.note-judge .nl { color: var(--text-tertiary); font-size: 11px; font-weight: 600; flex-shrink: 0; min-width: 56px; padding-top: 2px; }
.note-judge .nv { color: var(--text-primary); flex: 1; }
.note-foot { padding: 10px 16px; border-top: 1px solid var(--border-light); font-size: 11px; color: var(--text-tertiary); display: flex; justify-content: space-between; align-items: center; }
.note-time { flex-shrink: 0; }
.note-foot-actions { display: flex; align-items: center; gap: 10px; }
.foot-link { background: none; border: none; color: var(--text-tertiary); cursor: pointer; font-size: 11px; padding: 0; }
.foot-link:hover { color: var(--primary); }
.detail-link { color: var(--primary); font-weight: 500; }

.empty { grid-column: 1 / -1; text-align: center; color: var(--text-tertiary); padding: 40px; }

/* 详情抽屉 */
.drawer-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; justify-content: flex-end; z-index: 1000; }
.drawer { width: 560px; max-width: 94vw; height: 100%; background: var(--bg-elevated); display: flex; flex-direction: column; box-shadow: -4px 0 24px rgba(0,0,0,0.15); }
.drawer-head { padding: 16px 20px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center; }
.drawer-title { display: flex; align-items: center; gap: 8px; font-size: 15px; }
.drawer-body { padding: 20px; overflow-y: auto; flex: 1; }
.d-sec { margin-bottom: 16px; }
.d-cardinfo { margin-bottom: 16px; padding: 12px 14px; background: var(--bg-subtle); border-radius: var(--radius-md); border: 1px solid var(--border-light); }
.d-summary { font-size: 13px; line-height: 1.65; color: var(--text-secondary); margin: 0 0 8px; }
.d-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.d-tagchip { font-size: 11px; padding: 2px 9px; border-radius: 999px; background: var(--primary-soft, rgba(99,102,241,0.1)); color: var(--primary); font-weight: 600; }
.d-sec.warn .d-label { color: var(--danger); }
.d-sec.tip .d-label { color: var(--success); }
.d-label { font-size: 12px; font-weight: 700; color: var(--text-secondary); margin-bottom: 6px; }
.d-code { font-size: 12px; background: var(--bg-subtle); padding: 10px 12px; border-radius: var(--radius-md); white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; }
.d-link { margin-top: 8px; }

/* 编辑弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-elevated); border-radius: var(--radius-lg); width: 600px; max-width: 92vw; max-height: 86vh; display: flex; flex-direction: column; }
.modal.wide { width: 960px; }
.modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-body { padding: 20px; overflow-y: auto; flex: 1; }
.edit-body { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 800px) { .edit-body { grid-template-columns: 1fr; } }
.edit-form { display: flex; flex-direction: column; gap: 12px; }
.form-group label { display: block; margin-bottom: 5px; font-size: 12px; color: var(--text-secondary); font-weight: 600; }
.form-group textarea { width: 100%; padding: 8px 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 13px; background: var(--bg-base); color: var(--text-primary); font-family: inherit; resize: vertical; }
.form-group textarea:focus { outline: none; border-color: var(--primary); }
.edit-preview { border-left: 1px solid var(--border-light); padding-left: 20px; max-height: 60vh; overflow: hidden; display: flex; flex-direction: column; }
.np-title { font-size: 12px; color: var(--text-tertiary); font-weight: 700; margin-bottom: 10px; }
.np-scroll { overflow-y: auto; flex: 1; padding-right: 6px; }
.modal-footer { padding: 16px 20px; border-top: 1px solid var(--border-light); display: flex; justify-content: flex-end; gap: 8px; }

.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-primary { background: var(--primary); color: #fff; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-icon { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; }
</style>
