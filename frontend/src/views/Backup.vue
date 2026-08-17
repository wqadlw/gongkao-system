<template>
  <div class="backup-page">
    <div class="page-header">
      <h2>💾 数据备份与导出</h2>
    </div>

    <div class="card">
      <div class="card-header"><h3>📦 数据库信息</h3></div>
      <div class="card-body">
        <div class="info-list">
          <div class="info-row"><span class="info-label">数据库路径</span><span class="info-value">{{ info.db_path }}</span></div>
          <div class="info-row"><span class="info-label">数据库大小</span><span class="info-value">{{ info.db_size }}</span></div>
          <div class="info-row"><span class="info-label">最后修改</span><span class="info-value">{{ info.last_modified }}</span></div>
          <div class="info-row"><span class="info-label">存储方式</span><span class="info-value">本地SQLite单文件</span></div>
        </div>
        <div class="action-buttons">
          <button class="btn-primary" @click="createBackup">💾 立即备份</button>
          <button class="btn-default" @click="loadBackups">🔄 刷新备份列表</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3>📋 备份记录</h3></div>
      <div class="card-body">
        <table class="data-table">
          <thead>
            <tr><th>备份文件</th><th width="120">大小</th><th width="180">备份时间</th><th width="180">操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="b in backups" :key="b.filename">
              <td class="file-name">{{ b.filename }}</td>
              <td>{{ b.size }}</td>
              <td class="time-cell">{{ b.time }}</td>
              <td>
                <button class="btn-default small" @click="restoreBackup(b)">恢复</button>
                <button class="btn-icon danger" @click="deleteBackup(b)">🗑️</button>
              </td>
            </tr>
            <tr v-if="backups.length === 0"><td colspan="4" class="empty">暂无备份记录</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3>📤 数据导出</h3></div>
      <div class="card-body">
        <div class="export-buttons">
          <button class="btn-default" @click="exportAll">📋 导出全部数据(JSON)</button>
          <button class="btn-default" @click="exportQuestions">📝 导出题目(Markdown)</button>
          <button class="btn-default" @click="exportNotes">📓 导出笔记(Markdown)</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { backupApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const info = ref({})
const backups = ref([])

async function loadInfo() {
  const res = await backupApi.info()
  info.value = res.data
}

async function loadBackups() {
  const res = await backupApi.list()
  backups.value = res.data
}

async function createBackup() {
  const res = await backupApi.create()
  ElMessage.success(res.data.message)
  loadBackups()
}

async function restoreBackup(row) {
  await ElMessageBox.confirm('恢复将覆盖当前数据库，确定继续？', '警告', { type: 'warning' })
  await backupApi.restore(row.filename)
  ElMessage.success('恢复成功，请重启系统')
}

async function deleteBackup(row) {
  await ElMessageBox.confirm('确定删除此备份？', '提示', { type: 'warning' })
  await backupApi.delete(row.filename)
  ElMessage.success('删除成功')
  loadBackups()
}

async function exportAll() {
  const res = await backupApi.exportAll()
  const url = URL.createObjectURL(new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `gongkao_backup_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

async function exportQuestions() {
  try {
    const res = await backupApi.exportQuestions()
    const url = URL.createObjectURL(new Blob([res.data], { type: 'text/markdown' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `questions_${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch { ElMessage.error('导出失败') }
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
  } catch { ElMessage.error('导出失败') }
}

onMounted(() => { loadInfo(); loadBackups() })
</script>

<style scoped>
.backup-page { max-width: 900px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.card { background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light); margin-bottom: 16px; }
.card-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
.card-header h3 { margin: 0; font-size: 15px; font-weight: 600; }
.card-body { padding: 20px; }
.info-list { margin-bottom: 16px; }
.info-row { display: flex; padding: 8px 0; border-bottom: 1px solid var(--border-light); }
.info-row:last-child { border-bottom: none; }
.info-label { width: 120px; color: var(--text-secondary); font-size: 13px; }
.info-value { flex: 1; font-size: 13px; color: var(--text-primary); word-break: break-all; }
.action-buttons { display: flex; gap: 12px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: var(--bg-subtle); padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.data-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-light); font-size: 13px; }
.file-name { font-family: 'Consolas', monospace; font-size: 12px; }
.time-cell { font-size: 12px; color: var(--text-tertiary); }
.empty { text-align: center; color: var(--text-tertiary); padding: 20px; }
.btn-primary { background: var(--primary); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-default.small { padding: 4px 12px; font-size: 12px; }
.btn-icon { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; }
.btn-icon.danger:hover { background: var(--danger-bg); }
.export-buttons { display: flex; gap: 12px; flex-wrap: wrap; }
</style>
