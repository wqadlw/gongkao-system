<template>
  <div class="stages-page">
    <div class="page-header">
      <h2>📅 备考阶段管理</h2>
      <button class="btn-primary" @click="showCreate = true">+ 新增阶段</button>
    </div>

    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>阶段名称</th>
            <th width="120">开始日期</th>
            <th width="120">结束日期</th>
            <th width="100">每日目标</th>
            <th>目标</th>
            <th width="100">状态</th>
            <th width="160">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in stages" :key="s.id">
            <td>{{ s.name }}</td>
            <td class="time-cell">{{ s.start_date }}</td>
            <td class="time-cell">{{ s.end_date }}</td>
            <td>{{ s.daily_target }}题</td>
            <td>{{ s.goal || '-' }}</td>
            <td><span class="status-tag" :class="s.is_active ? 'active' : 'inactive'">{{ s.is_active ? '进行中' : '已结束' }}</span></td>
            <td>
              <button class="btn-default small" @click="toggleActive(s)">{{ s.is_active ? '结束' : '激活' }}</button>
              <button class="btn-icon danger" @click="deleteStage(s)">🗑️</button>
            </td>
          </tr>
          <tr v-if="stages.length === 0"><td colspan="7" class="empty">暂无备考阶段</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="showCreate" class="modal-overlay" @click="showCreate = false">
      <div class="modal" @click.stop>
        <div class="modal-header"><h3>新增备考阶段</h3><button class="btn-icon" @click="showCreate = false">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label>阶段名称</label><input v-model="form.name" placeholder="如：基础夯实期" /></div>
          <div class="form-row">
            <div class="form-group"><label>开始日期</label><input v-model="form.start_date" type="date" /></div>
            <div class="form-group"><label>结束日期</label><input v-model="form.end_date" type="date" /></div>
          </div>
          <div class="form-group"><label>每日目标（题）</label><input v-model.number="form.daily_target" type="number" /></div>
          <div class="form-group"><label>阶段目标</label><textarea v-model="form.goal" rows="3" placeholder="如：完成数量关系全部考点学习"></textarea></div>
          <div class="form-group"><label>备注</label><input v-model="form.remark" /></div>
        </div>
        <div class="modal-footer">
          <button class="btn-default" @click="showCreate = false">取消</button>
          <button class="btn-primary" @click="saveStage">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { studyApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const stages = ref([])
const showCreate = ref(false)
const form = ref({
  name: '', start_date: new Date().toISOString().slice(0, 10), end_date: '',
  daily_target: 20, goal: '', remark: ''
})

async function loadStages() {
  const res = await studyApi.getStages()
  stages.value = res.data
}

async function saveStage() {
  if (!form.value.name) { ElMessage.warning('请填写阶段名称'); return }
  await studyApi.createStage(form.value)
  ElMessage.success('创建成功')
  showCreate.value = false
  loadStages()
  form.value = { name: '', start_date: new Date().toISOString().slice(0, 10), end_date: '', daily_target: 20, goal: '', remark: '' }
}

async function toggleActive(row) {
  await studyApi.updateStage(row.id, { is_active: !row.is_active })
  ElMessage.success('更新成功')
  loadStages()
}

async function deleteStage(row) {
  await ElMessageBox.confirm('确定删除此阶段？', '提示', { type: 'warning' })
  await studyApi.deleteStage(row.id)
  ElMessage.success('删除成功')
  loadStages()
}

onMounted(loadStages)
</script>

<style scoped>
.stages-page { max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.table-card { background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { background: var(--bg-subtle); padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.data-table td { padding: 12px 16px; border-bottom: 1px solid var(--border-light); font-size: 13px; }
.time-cell { font-size: 12px; color: var(--text-tertiary); }
.status-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.status-tag.active { background: var(--success-bg); color: var(--success); }
.status-tag.inactive { background: var(--bg-subtle); color: var(--text-tertiary); }
.empty { text-align: center; color: var(--text-tertiary); padding: 40px; }
.btn-primary { background: var(--primary); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-default.small { padding: 4px 12px; font-size: 12px; }
.btn-icon { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; }
.btn-icon.danger:hover { background: var(--danger-bg); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-elevated); border-radius: var(--radius-lg); width: 560px; max-width: 90vw; }
.modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-body { padding: 20px; }
.modal-footer { padding: 16px 20px; border-top: 1px solid var(--border-light); display: flex; justify-content: flex-end; gap: 8px; }
.form-group { margin-bottom: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group label { display: block; margin-bottom: 6px; font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.form-group input, .form-group textarea { width: 100%; padding: 8px 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 14px; background: var(--bg-base); color: var(--text-primary); font-family: inherit; }
.form-group textarea { resize: vertical; }
</style>
