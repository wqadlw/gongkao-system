<template>
  <div class="countdown-page">
    <div class="page-header">
      <h2>⏰ 考试倒计时</h2>
      <button class="btn-primary" @click="showCreate = true">+ 添加考试</button>
    </div>

    <!-- 倒计时卡片 -->
    <div class="exam-grid">
      <div v-for="exam in exams" :key="exam.id" class="exam-card" :class="[exam.exam_type, { passed: exam.is_passed }]">
        <div class="exam-card-bg"></div>
        <div class="exam-card-content">
          <div class="exam-type-tag">{{ exam.exam_type }}</div>
          <div class="exam-name">{{ exam.name }}</div>
          <div class="exam-days" v-if="!exam.is_passed">
            <span class="days-num">{{ exam.days_left }}</span>
            <span class="days-unit">天</span>
          </div>
          <div class="exam-days passed" v-else>
            <span class="days-num">已结束</span>
          </div>
          <div class="exam-date">📅 {{ exam.exam_date }}</div>
          <div class="exam-remark" v-if="exam.remark">{{ exam.remark }}</div>
          <div class="exam-actions">
            <button class="btn-text" @click="editExam(exam)">编辑</button>
            <button class="btn-text danger" @click="deleteExam(exam)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 备考建议 -->
    <div class="card" v-if="nearestExam">
      <div class="card-header"><h3>📋 备考阶段建议</h3></div>
      <div class="card-body">
        <div class="advice-list">
          <div class="advice-item" v-if="nearestExam.days_left > 180">
            <span class="advice-phase">基础阶段</span>
            <span class="advice-text">系统学习各模块基础知识，建立知识框架，每天保证2-3小时学习时间</span>
          </div>
          <div class="advice-item" v-if="nearestExam.days_left > 90 && nearestExam.days_left <= 180">
            <span class="advice-phase">强化阶段</span>
            <span class="advice-text">专项突破薄弱模块，大量刷题巩固，总结解题方法和技巧</span>
          </div>
          <div class="advice-item" v-if="nearestExam.days_left > 30 && nearestExam.days_left <= 90">
            <span class="advice-phase">冲刺阶段</span>
            <span class="advice-text">真题模拟，限时训练，查漏补缺，重点复习错题和高频考点</span>
          </div>
          <div class="advice-item" v-if="nearestExam.days_left <= 30 && nearestExam.days_left > 0">
            <span class="advice-phase">临考阶段</span>
            <span class="advice-text">保持手感，回顾笔记，调整心态，保证作息规律</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <div v-if="showCreate" class="modal-overlay" @click="showCreate = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>{{ editId ? '编辑考试' : '添加考试' }}</h3>
          <button class="btn-text" @click="showCreate = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>考试名称</label>
            <input v-model="form.name" placeholder="如：2027年国家公务员考试" />
          </div>
          <div class="form-group">
            <label>考试类型</label>
            <select v-model="form.exam_type">
              <option value="国考">国考</option>
              <option value="省考">省考</option>
              <option value="事业编">事业编</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label>考试日期</label>
            <input v-model="form.exam_date" type="date" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <input v-model="form.remark" placeholder="如：预计日期，实际以公告为准" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-default" @click="showCreate = false">取消</button>
          <button class="btn-primary" @click="saveExam">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { examApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const exams = ref([])
const showCreate = ref(false)
const editId = ref(null)
const form = ref({
  name: '', exam_type: '国考',
  exam_date: new Date().toISOString().slice(0, 10), remark: ''
})

const nearestExam = computed(() => {
  const active = exams.value.filter(e => !e.is_passed && e.days_left >= 0)
  return active.length > 0 ? active[0] : null
})

async function loadExams() {
  const res = await examApi.getList()
  exams.value = res.data
}

function editExam(exam) {
  editId.value = exam.id
  form.value = {
    name: exam.name, exam_type: exam.exam_type,
    exam_date: exam.exam_date, remark: exam.remark
  }
  showCreate.value = true
}

async function saveExam() {
  if (!form.value.name || !form.value.exam_date) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (editId.value) {
    await examApi.update(editId.value, form.value)
    ElMessage.success('更新成功')
  } else {
    await examApi.create(form.value)
    ElMessage.success('添加成功')
  }
  showCreate.value = false
  editId.value = null
  form.value = {
    name: '', exam_type: '国考',
    exam_date: new Date().toISOString().slice(0, 10), remark: ''
  }
  loadExams()
}

async function deleteExam(exam) {
  await ElMessageBox.confirm(`确定删除【${exam.name}】？`, '提示', { type: 'warning' })
  await examApi.delete(exam.id)
  ElMessage.success('删除成功')
  loadExams()
}

onMounted(loadExams)
</script>

<style scoped>
.countdown-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}
.exam-card {
  border-radius: var(--radius-xl);
  padding: 28px;
  position: relative;
  overflow: hidden;
  color: white;
  min-height: 200px;
}
.exam-card.国考 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.exam-card.省考 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}
.exam-card.事业编 {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}
.exam-card.其他 {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}
.exam-card.passed {
  filter: grayscale(0.6);
  opacity: 0.7;
}
.exam-card-bg {
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
  border-radius: 50%;
}
.exam-card-content {
  position: relative;
  z-index: 1;
}
.exam-type-tag {
  display: inline-block;
  background: rgba(255,255,255,0.25);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}
.exam-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}
.exam-days {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}
.days-num {
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.days-unit {
  font-size: 20px;
  opacity: 0.9;
}
.exam-days.passed .days-num {
  font-size: 28px;
  opacity: 0.8;
}
.exam-date {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 4px;
}
.exam-remark {
  font-size: 12px;
  opacity: 0.7;
  margin-bottom: 12px;
}
.exam-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.btn-text {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
}
.btn-text:hover {
  background: rgba(255,255,255,0.3);
}
.btn-text.danger:hover {
  background: rgba(239,68,68,0.6);
}

.card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  overflow: hidden;
}
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}
.card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.card-body {
  padding: 16px 20px;
}
.advice-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.advice-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--bg-subtle);
  border-radius: var(--radius-md);
}
.advice-phase {
  background: var(--primary);
  color: white;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}
.advice-text {
  color: var(--text-secondary);
  font-size: 14px;
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
.btn-primary:hover {
  background: var(--primary-dark);
}
.btn-default {
  background: var(--bg-subtle);
  color: var(--text-secondary);
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
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
  width: 480px;
  max-width: 90vw;
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
.form-group input, .form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-base);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: var(--bg-base);
  color: var(--text-primary);
}
.form-group input:focus, .form-group select:focus {
  outline: none;
  border-color: var(--primary);
}
</style>
