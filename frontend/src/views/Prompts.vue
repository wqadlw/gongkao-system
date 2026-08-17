<template>
  <div class="prompts-page">
    <div class="page-header">
      <h2>📝 提示词模板管理</h2>
      <button class="btn-primary" @click="showCreate = true">+ 新建模板</button>
    </div>

    <div class="info-banner">
      <strong>💡 使用流程：</strong>复制通用提示词 → 粘贴到外部AI + 发送题目截图 → AI<strong>自动判定模块与考点</strong>、按「题目 + 一~六节」结构化Markdown作答（支持LaTeX公式） → 粘贴回"题目录入"页 → 系统自动归类入库
    </div>

    <!-- 模块筛选 -->
    <div class="filter-tabs">
      <button v-for="t in types" :key="t.value" 
        :class="['tab', { active: filterType === t.value }]"
        @click="filterType = t.value; loadList()">
        {{ t.label }}
      </button>
    </div>

    <!-- 模板列表 -->
    <div class="prompt-grid">
      <div v-for="p in prompts" :key="p.id" class="prompt-card">
        <div class="prompt-header">
          <div class="prompt-title">
            <span v-if="p.is_locked" class="lock-badge">🔒内置</span>
            <span v-if="p.is_pinned" class="pin-badge">📌</span>
            {{ p.name }}
          </div>
          <div class="prompt-actions">
            <button class="btn-icon" @click="copyPrompt(p)" title="复制纯提示词">📋</button>
            <button class="btn-icon" @click="openBuild(p)" title="组装提问文本">🔧</button>
            <button v-if="!p.is_locked" class="btn-icon" @click="editPrompt(p)">✏️</button>
            <button v-if="!p.is_locked" class="btn-icon danger" @click="deletePrompt(p)">🗑️</button>
          </div>
        </div>
        <div class="prompt-meta">
          <span class="tag" :class="p.type">{{ p.type }}</span>
          <span v-if="p.tag" class="tag-default">{{ p.tag }}</span>
        </div>
        <div class="prompt-preview">{{ p.content.slice(0, 150) }}...</div>
        <div class="prompt-remark" v-if="p.remark">💡 {{ p.remark }}</div>
      </div>
    </div>

    <!-- 组装提问文本对话框 -->
    <div v-if="showBuild" class="modal-overlay" @click="showBuild = false">
      <div class="modal large" @click.stop>
        <div class="modal-header">
          <h3>🔧 组装提问文本 - {{ currentPrompt?.name }}</h3>
          <button class="btn-text" @click="showBuild = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>题目内容（粘贴题干+选项，或描述截图内容）</label>
            <textarea v-model="buildForm.question_content" rows="8" 
              placeholder="粘贴题目文本，或描述截图中的题目内容..."></textarea>
          </div>
          <div class="built-result" v-if="builtText">
            <div class="built-header">
              <span>组装结果（复制后发送给AI）</span>
              <button class="btn-primary small" @click="copyBuilt">📋 复制</button>
            </div>
            <pre class="built-text">{{ builtText }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <div v-if="showCreate" class="modal-overlay" @click="showCreate = false">
      <div class="modal large" @click.stop>
        <div class="modal-header">
          <h3>{{ editId ? '编辑模板' : '新建模板' }}</h3>
          <button class="btn-text" @click="showCreate = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模板名称</label>
            <input v-model="form.name" placeholder="如：【数量关系】工程问题解析模板" />
          </div>
          <div class="form-group">
            <label>模块类型</label>
            <select v-model="form.type">
              <option v-for="t in types.slice(1)" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>标签</label>
            <input v-model="form.tag" placeholder="如：基础/拔高/通用" />
          </div>
          <div class="form-group">
            <label>提示词内容</label>
            <textarea v-model="form.content" rows="15" 
              placeholder="输入提示词内容，使用 {question_content} 作为题目占位符..."></textarea>
          </div>
          <div class="form-group">
            <label>备注</label>
            <input v-model="form.remark" placeholder="模板说明" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-default" @click="showCreate = false">取消</button>
          <button class="btn-primary" @click="savePrompt">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { promptApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const prompts = ref([])
const filterType = ref('')
const showCreate = ref(false)
const showBuild = ref(false)
const editId = ref(null)
const currentPrompt = ref(null)
const builtText = ref('')
const form = ref({ name: '', type: '数量关系', tag: '', content: '', remark: '' })
const buildForm = ref({ question_content: '' })

const types = [
  { value: '', label: '全部' },
  { value: '政治理论', label: '政治理论' },
  { value: '常识判断', label: '常识判断' },
  { value: '言语理解与表达', label: '言语理解' },
  { value: '数量关系', label: '数量关系' },
  { value: '判断推理', label: '判断推理' },
  { value: '资料分析', label: '资料分析' },
]

async function loadList() {
  const res = await promptApi.getList(filterType.value || undefined)
  prompts.value = res.data
}

async function copyPrompt(p) {
  try {
    await navigator.clipboard.writeText(p.content)
    ElMessage.success('提示词已复制，去粘贴给AI吧')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

async function openBuild(p) {
  currentPrompt.value = p
  buildForm.value = { question_content: '' }
  builtText.value = ''
  showBuild.value = true
  // 自动构建
  const res = await promptApi.build(p.id, buildForm.value)
  builtText.value = res.data.text
}

async function copyBuilt() {
  try {
    await navigator.clipboard.writeText(builtText.value)
    ElMessage.success('已复制完整提问文本')
  } catch {
    ElMessage.warning('复制失败')
  }
}

function editPrompt(p) {
  editId.value = p.id
  form.value = { name: p.name, type: p.type, tag: p.tag, content: p.content, remark: p.remark }
  showCreate.value = true
}

async function savePrompt() {
  if (!form.value.name || !form.value.content) {
    ElMessage.warning('请填写名称和内容')
    return
  }
  if (editId.value) {
    await promptApi.update(editId.value, form.value)
    ElMessage.success('更新成功')
  } else {
    await promptApi.create(form.value)
    ElMessage.success('创建成功')
  }
  showCreate.value = false
  editId.value = null
  form.value = { name: '', type: '数量关系', tag: '', content: '', remark: '' }
  loadList()
}

async function deletePrompt(p) {
  await ElMessageBox.confirm(`确定删除【${p.name}】？`, '提示', { type: 'warning' })
  await promptApi.delete(p.id)
  ElMessage.success('删除成功')
  loadList()
}

onMounted(loadList)
</script>

<style scoped>
.prompts-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.info-banner {
  background: var(--primary-bg);
  color: var(--primary-dark);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 13px;
  margin-bottom: 20px;
  border-left: 3px solid var(--primary);
}

.filter-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.tab {
  padding: 6px 16px;
  border: 1px solid var(--border-base);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.tab.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.prompt-card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}
.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}
.prompt-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.lock-badge {
  background: var(--warning-bg);
  color: var(--warning);
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}
.pin-badge {
  font-size: 14px;
}
.prompt-actions {
  display: flex;
  gap: 4px;
}
.btn-icon {
  background: var(--bg-subtle);
  border: none;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
}
.btn-icon:hover {
  background: var(--primary-bg);
}
.btn-icon.danger:hover {
  background: var(--danger-bg);
}
.prompt-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}
.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.tag.政治理论 { background: var(--danger-bg); color: var(--danger); }
.tag.常识判断 { background: var(--warning-bg); color: var(--warning); }
.tag.言语理解与表达 { background: var(--primary-bg); color: var(--primary); }
.tag.数量关系 { background: var(--success-bg); color: var(--success); }
.tag.判断推理 { background: var(--info-bg); color: var(--info); }
.tag.资料分析 { background: #fce7f3; color: #db2777; }
.tag-default {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-subtle);
  color: var(--text-secondary);
}
.prompt-preview {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-height: 80px;
  overflow: hidden;
}
.prompt-remark {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
}

.btn-primary {
  background: var(--primary);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary.small { padding: 4px 12px; font-size: 12px; }
.btn-default {
  background: var(--bg-subtle);
  color: var(--text-secondary);
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
}
.btn-text {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-secondary);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  width: 600px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.modal.large {
  width: 800px;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}
.modal-header h3 {
  margin: 0;
  font-size: 16px;
}
.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}
.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}
.form-group input, .form-group textarea, .form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: inherit;
}
.form-group textarea {
  resize: vertical;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}
.form-group input:focus, .form-group textarea:focus, .form-group select:focus {
  outline: none;
  border-color: var(--primary);
}

.built-result {
  margin-top: 16px;
}
.built-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.built-text {
  background: var(--bg-base);
  padding: 12px;
  border-radius: var(--radius-md);
  max-height: 300px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  border: 1px solid var(--border-light);
}
</style>
