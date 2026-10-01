import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '首页看板' } },
  { path: '/prompts', name: 'Prompts', component: () => import('../views/Prompts.vue'), meta: { title: '提示词管理' } },
  { path: '/question-input', name: 'QuestionInput', component: () => import('../views/QuestionInput.vue'), meta: { title: '题目录入' } },
  { path: '/deposit', name: 'Deposit', component: () => import('../views/Deposit.vue'), meta: { title: '解析沉淀' } },
  { path: '/question-list', name: 'QuestionList', component: () => import('../views/QuestionList.vue'), meta: { title: '题库列表' } },
  { path: '/question-bank', name: 'QuestionBank', component: () => import('../views/QuestionBank.vue'), meta: { title: '真题库对接' } },
  { path: '/knowledge', name: 'Knowledge', component: () => import('../views/Knowledge.vue'), meta: { title: '行测知识库' } },
  { path: '/resource-library', name: 'ResourceLibrary', component: () => import('../views/ResourceLibrary.vue'), meta: { title: '行测资料库' } },
  { path: '/solve-library', name: 'SolveLibrary', component: () => import('../views/SolveLibrary.vue'), meta: { title: '行测解题库' } },
  { path: '/question/:id', name: 'QuestionDetail', component: () => import('../views/QuestionDetail.vue'), meta: { title: '题目详情' } },
  { path: '/search', name: 'Search', component: () => import('../views/Search.vue'), meta: { title: '全局搜索' } },
  { path: '/errors', name: 'Errors', component: () => import('../views/Errors.vue'), meta: { title: '错题集' } },
  { path: '/notes', name: 'Notes', component: () => import('../views/Notes.vue'), meta: { title: '笔记管理' } },
  { path: '/review', name: 'Review', component: () => import('../views/Review.vue'), meta: { title: '智能复习' } },
  { path: '/mock', name: 'MockExam', component: () => import('../views/MockExam.vue'), meta: { title: '模考模式' } },
  { path: '/favorites', name: 'Favorites', component: () => import('../views/Favorites.vue'), meta: { title: '我的收藏' } },
  { path: '/stages', name: 'Stages', component: () => import('../views/Stages.vue'), meta: { title: '备考阶段' } },
  { path: '/visualization', name: 'Visualization', component: () => import('../views/Visualization.vue'), meta: { title: '可视化大屏' } },
  { path: '/countdown', name: 'Countdown', component: () => import('../views/Countdown.vue'), meta: { title: '考试倒计时' } },
  { path: '/backup', name: 'Backup', component: () => import('../views/Backup.vue'), meta: { title: '备份导出' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
