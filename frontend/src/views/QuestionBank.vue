<template>
  <div class="bank-page">
    <div class="page-header">
      <h2><el-icon><Collection /></el-icon> 真题库对接</h2>
      <span v-if="status.available" class="bank-meta">共 {{ totalFileCount }} 份试卷 · {{ status.root }}</span>
      <div class="header-spacer"></div>
      <el-button size="small" @click="openDatasetDialog"><el-icon><Box /></el-icon> 数据集导入</el-button>
    </div>

    <!-- 数据集导入对话框 -->
    <el-dialog v-model="datasetVisible" title="通用数据集导入" width="560px">
      <div class="ds-hint">把 C-Eval / Xiezhi 等数据集（JSON/CSV/Parquet）放到 <code>{{ datasetDir || 'data/question_sources/' }}</code> 后刷新即可识别。</div>
      <el-table :data="datasets" size="small" highlight-current-row @current-change="row => (datasetPicked = row)" v-loading="datasetLoading">
        <el-table-column prop="file" label="文件" min-width="220" />
        <el-table-column prop="count" label="题数" width="70" />
        <el-table-column prop="size_kb" label="大小(KB)" width="90" />
        <el-table-column label="状态" width="70">
          <template #default="s"><span v-if="s.row.error" class="ds-err">解析失败</span><span v-else>可用</span></template>
        </el-table-column>
      </el-table>
      <div class="ds-form">
        <el-input v-model="datasetLevel1" placeholder="一级考点（默认：常识判断）" size="small" style="width: 220px" />
        <el-input-number v-model="datasetLimit" :min="0" size="small" style="width: 140px" placeholder="0=全部" />
        <el-button type="primary" size="small" :disabled="!datasetPicked" :loading="datasetImporting" @click="doImportDataset">
          <el-icon><Download /></el-icon> 导入选中
        </el-button>
      </div>
    </el-dialog>

    <div v-if="!status.available" class="card">
      <div class="card-body bank-missing">
        <p>未找到真题仓库目录，请先克隆：</p>
        <pre>git clone https://github.com/ERRRC/xingcezhenti.git {{ status.root }}</pre>
        <p class="hint">也可通过环境变量 <code>XINGCE_BANK_DIR</code> 指定仓库位置，修改后重启后端。</p>
      </div>
    </div>

    <div v-else class="bank-layout">
      <!-- 左侧：模块 + 试卷列表 -->
      <aside class="card bank-side">
        <div class="bank-modules">
          <button
            v-for="m in status.modules" :key="m.dir"
            class="module-item" :class="{ active: m.dir === currentModule }"
            @click="pickModule(m.dir)"
          >
            <span>{{ m.name }}</span>
            <span class="module-count">{{ m.file_count }}</span>
          </button>
        </div>
        <div class="bank-search">
          <el-input v-model="keyword" placeholder="搜索试卷名称（年份/地区）" clearable @input="onSearchInput">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
        <div v-loading="filesLoading" class="bank-files">
          <button
            v-for="f in files" :key="f.file"
            class="file-item" :class="{ active: f.file === currentFile }"
            @click="pickFile(f)"
          >
            <span class="file-title">{{ f.title }}</span>
            <span v-if="f.imported_count" class="file-badge">已录 {{ f.imported_count }}</span>
          </button>
          <div v-if="!filesLoading && files.length === 0" class="empty-tip">无匹配试卷</div>
        </div>
        <el-pagination
          v-if="filesTotal > filesPageSize" layout="prev, pager, next" small
          :total="filesTotal" :page-size="filesPageSize" :current-page="filesPage"
          @current-change="p => { filesPage = p; loadFiles() }"
        />
      </aside>

      <!-- 右侧：试卷题目 -->
      <section class="bank-main">
        <div class="card bank-toolbar">
          <div class="toolbar-row">
            <div class="toolbar-title">{{ currentFileTitle || '选择左侧试卷' }}</div>
            <div class="toolbar-actions">
              <el-button size="small" @click="showTree = !showTree">
                <el-icon><Aim /></el-icon> 考点：{{ targetPathLabel }}
              </el-button>
              <el-button type="primary" size="small" :disabled="!selectedCount" :loading="importing" @click="doImport(false)">
                <el-icon><Download /></el-icon> 导入选中（{{ selectedCount }}）
              </el-button>
              <el-button size="small" :disabled="!notImportedCount" :loading="importing" @click="doImport(true)">
                <el-icon><Download /></el-icon> 导入全部未录（{{ notImportedCount }}）
              </el-button>
            </div>
          </div>
          <div v-if="showTree" class="toolbar-tree">
            <div class="tree-hint">点击节点选择导入目标考点（默认按模块一级考点）</div>
            <CategoryTree :nodes="categoryTree" selectable @select="onPickCategory" />
          </div>
        </div>

        <div v-loading="detailLoading" class="bank-questions">
          <div
            v-for="(q, idx) in questions" :key="q.no"
            class="card bank-question animate__animated animate__fadeInUp animate__faster"
            :class="{ imported: q.imported }"
            :style="{ animationDelay: Math.min(idx * 45, 450) + 'ms' }"
          >
            <div class="q-head">
              <el-checkbox :model-value="checked.includes(q.no)" :disabled="q.imported" @change="v => toggleCheck(q.no, v)" />
              <span class="q-no">第 {{ q.no }} 题</span>
              <span v-if="q.subtype" class="q-tag">{{ q.subtype }}</span>
              <span v-if="q.material_no" class="q-tag material">材料 {{ q.material_no }}</span>
              <span class="q-qid">qid {{ q.qid }}</span>
              <span v-if="q.imported" class="q-imported">✓ 已入库</span>
              <span class="q-answer">答案：<b>{{ q.answer }}</b></span>
            </div>
            <div v-if="q.material" class="q-material md-body" v-html="md(q.material)"></div>
            <div class="q-stem md-body" v-html="md(q.stem)"></div>
            <ul class="q-options">
              <li
                v-for="opt in q.options" :key="opt.label"
                :class="{ correct: opt.correct }"
              >
                <b>{{ opt.label }}.</b>
                <span class="md-body md-inline" v-html="mdi(opt.text)"></span>
                <span v-if="opt.correct" class="opt-mark">✓</span>
              </li>
            </ul>
            <details v-if="q.analysis" class="q-analysis">
              <summary>官方解析</summary>
              <div class="md-body" v-html="md(q.analysis)"></div>
            </details>
          </div>
          <div v-if="!detailLoading && questions.length === 0" class="empty-tip">左侧选择一份试卷查看题目</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { bankApi, categoryApi } from '../api'
import { renderMarkdown, renderInline } from '../utils/md'
import CategoryTree from '../components/CategoryTree.vue'

const md = renderMarkdown
const mdi = renderInline

const status = ref({ available: false, root: '', modules: [] })
const keyword = ref('')
const currentModule = ref('')
const files = ref([])
const filesTotal = ref(0)
const filesPage = ref(1)
const filesPageSize = 50
const filesLoading = ref(false)
const currentFile = ref('')
const detailLoading = ref(false)
const detail = ref(null)
const questions = computed(() => detail.value ? detail.value.questions : [])
const checked = ref([])
const importing = ref(false)
const showTree = ref(false)
const categoryTree = ref([])
const targetLevels = ref(['', '', '', '', ''])
const datasetVisible = ref(false)
const datasetLoading = ref(false)
const datasetImporting = ref(false)
const datasets = ref([])
const datasetDir = ref('')
const datasetPicked = ref(null)
const datasetLevel1 = ref('')
const datasetLimit = ref(0)

const totalFileCount = computed(() => status.value.modules.reduce((s, m) => s + m.file_count, 0))
const currentFileTitle = computed(() => detail.value ? (detail.value.meta['试卷'] || currentFile.value) : '')
const selectedCount = computed(() => {
  if (!detail.value) return 0
  return questions.value.filter(q => checked.value.includes(q.no) && !q.imported).length
})
const notImportedCount = computed(() => questions.value.filter(q => !q.imported).length)
const targetPathLabel = computed(() => {
  const path = targetLevels.value.filter(Boolean)
  return path.length ? path.join(' / ') : '按模块'
})

function pickModule(dir) {
  currentModule.value = dir
  currentFile.value = ''
  detail.value = null
  filesPage.value = 1
  loadFiles()
}

let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { filesPage.value = 1; loadFiles() }, 300)
}

async function loadFiles() {
  filesLoading.value = true
  try {
    const res = await bankApi.files({ module: currentModule.value, keyword: keyword.value, page: filesPage.value, page_size: filesPageSize })
    files.value = res.data.items
    filesTotal.value = res.data.total
  } catch (e) {
    ElMessage.error('加载试卷列表失败')
  } finally {
    filesLoading.value = false
  }
}

async function pickFile(f) {
  currentFile.value = f.file
  checked.value = []
  detailLoading.value = true
  try {
    const res = await bankApi.file({ module: currentModule.value, name: f.file })
    detail.value = res.data
  } catch (e) {
    ElMessage.error('解析试卷失败')
  } finally {
    detailLoading.value = false
  }
}

function toggleCheck(no, v) {
  if (v) checked.value.push(no)
  else checked.value = checked.value.filter(n => n !== no)
}

function onPickCategory(node) {
  targetLevels.value = [node.level1 || '', node.level2 || '', node.level3 || '', node.level4 || '', node.level5 || '']
  showTree.value = false
  ElMessage.success(`导入考点：${targetPathLabel.value}`)
}

async function doImport(all) {
  const indexes = all ? [] : questions.value.filter(q => checked.value.includes(q.no) && !q.imported).map(q => q.no)
  if (!all && indexes.length === 0) return
  importing.value = true
  try {
    const [l1, l2, l3, l4, l5] = targetLevels.value
    const res = await bankApi.import({
      module: currentModule.value, name: currentFile.value, indexes,
      level1: l1 || defaultLevel1(),
      level2: l2, level3: l3, level4: l4, level5: l5,
    })
    ElMessage.success(`已导入 ${res.data.count} 题${res.data.skipped.length ? `，跳过 ${res.data.skipped.length} 题（已入库）` : ''}`)
    checked.value = []
    await pickFile({ file: currentFile.value })
    await loadFiles()
  } catch (e) {
    ElMessage.error('导入失败：' + (e.response?.data?.detail || '未知错误'))
  } finally {
    importing.value = false
  }
}

function defaultLevel1() {
  const m = status.value.modules.find(x => x.dir === currentModule.value)
  return m ? m.name : ''
}

async function openDatasetDialog() {
  datasetVisible.value = true
  datasetLoading.value = true
  try {
    const res = await bankApi.datasets()
    datasets.value = res.data.items
    datasetDir.value = res.data.dir
  } catch { ElMessage.error('数据集列表加载失败') }
  finally { datasetLoading.value = false }
}

async function doImportDataset() {
  if (!datasetPicked.value) return
  datasetImporting.value = true
  try {
    const res = await bankApi.importDataset({
      file: datasetPicked.value.file,
      level1: datasetLevel1.value,
      limit: datasetLimit.value || 0,
    })
    ElMessage.success(`已导入 ${res.data.imported} 题，跳过 ${res.data.skipped} 题（重复）`)
  } catch (e) {
    ElMessage.error('导入失败：' + (e.response?.data?.detail || '未知错误'))
  } finally { datasetImporting.value = false }
}

onMounted(async () => {
  try {
    const res = await bankApi.status()
    status.value = res.data
    if (res.data.available && res.data.modules.length) {
      pickModule(res.data.modules[0].dir)
    }
    const cats = await categoryApi.getTree()
    categoryTree.value = cats.data || []
  } catch (e) {
    ElMessage.error('真题库状态加载失败')
  }
})
</script>

<style scoped>
.bank-page { padding: 20px 24px; }
.page-header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-spacer { flex: 1; }
.ds-hint { font-size: 12px; color: var(--text-secondary, #666); margin-bottom: 10px; word-break: break-all; }
.ds-hint code { background: var(--bg-subtle, #f1f5f9); padding: 1px 5px; border-radius: 4px; }
.ds-err { color: var(--danger, #ef4444); font-size: 12px; }
.ds-form { display: flex; gap: 10px; align-items: center; margin-top: 12px; }
.bank-meta { font-size: 12px; color: var(--text-tertiary, #999); word-break: break-all; }
.bank-missing .hint { font-size: 12px; color: var(--text-tertiary, #999); }
.bank-missing pre { background: var(--bg-hover, #f5f5f5); padding: 10px 12px; border-radius: 8px; overflow: auto; }

.bank-layout { display: flex; gap: 16px; align-items: flex-start; }
.bank-side { width: 300px; flex-shrink: 0; display: flex; flex-direction: column; max-height: calc(100vh - 120px); }
.bank-modules { display: flex; flex-wrap: wrap; gap: 6px; padding: 12px; border-bottom: 1px solid var(--border-light, #eee); }
.module-item {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid var(--border-base, #ddd); background: transparent;
  border-radius: 14px; padding: 3px 10px; font-size: 12px; cursor: pointer; color: inherit;
}
.module-item.active { background: var(--primary, #409eff); border-color: var(--primary, #409eff); color: #fff; }
.module-count { font-size: 11px; opacity: .75; }
.bank-search { padding: 10px 12px 4px; }
.bank-files { flex: 1; overflow-y: auto; padding: 8px; }
.file-item {
  display: flex; flex-direction: column; align-items: flex-start; gap: 3px; width: 100%;
  text-align: left; background: transparent; border: none; border-radius: 8px;
  padding: 7px 9px; cursor: pointer; color: inherit; font-size: 12.5px; line-height: 1.45;
}
.file-item:hover { background: var(--bg-hover, #f5f5f5); }
.file-item.active { background: var(--primary-bg, rgba(64,158,255,.1)); }
.file-title { word-break: break-all; }
.file-badge { font-size: 11px; color: var(--success, #67c23a); }
.bank-side :deep(.el-pagination) { justify-content: center; padding: 8px 0; }

.bank-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.bank-toolbar { padding: 10px 14px; }
.toolbar-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.toolbar-title { font-weight: 600; font-size: 14px; min-width: 0; }
.toolbar-tree { margin-top: 10px; max-height: 300px; overflow: auto; border-top: 1px dashed var(--border-light, #eee); padding-top: 8px; }
.tree-hint { font-size: 12px; color: var(--text-tertiary, #999); margin-bottom: 6px; }

.bank-questions { display: flex; flex-direction: column; gap: 12px; padding-bottom: 24px; }
.bank-question { padding: 12px 14px; }
.bank-question.imported { opacity: .62; }
.q-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.q-no { font-weight: 600; }
.q-tag { font-size: 11px; padding: 1px 7px; border-radius: 10px; background: var(--bg-hover, #f0f0f0); color: var(--text-secondary, #666); }
.q-tag.material { background: rgba(230, 162, 60, .15); color: var(--warning, #e6a23c); }
.q-qid { font-size: 11px; color: var(--text-tertiary, #aaa); }
.q-imported { font-size: 12px; color: var(--success, #67c23a); }
.q-answer { margin-left: auto; font-size: 12.5px; color: var(--text-secondary, #666); }
.q-material { border-left: 3px solid var(--border-base, #ddd); padding-left: 10px; margin-bottom: 8px; font-size: 13px; }
.q-stem { font-size: 14px; }
.q-options { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.q-options li { display: flex; gap: 6px; align-items: baseline; font-size: 13.5px; border-radius: 6px; padding: 3px 8px; }
.q-options li.correct { background: rgba(103, 194, 58, .12); color: var(--success, #529b2e); }
.opt-mark { margin-left: auto; color: var(--success, #67c23a); font-weight: 700; }
.q-analysis { margin-top: 10px; font-size: 13px; }
.q-analysis summary { cursor: pointer; color: var(--primary, #409eff); font-size: 12.5px; user-select: none; }
.q-analysis .md-body { margin-top: 6px; padding-top: 6px; border-top: 1px dashed var(--border-light, #eee); }
.empty-tip { text-align: center; color: var(--text-tertiary, #999); padding: 30px 0; font-size: 13px; }

/* 题面内 HTML 图片自适应 */
.md-body :deep(img) { max-width: 100%; height: auto; }
</style>
