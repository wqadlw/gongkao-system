import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const categoryApi = {
  getTree: () => api.get('/categories/tree'),
  getList: () => api.get('/categories/list'),
  getModules: () => api.get('/categories/modules'),
  getNode: (id) => api.get('/categories/node/' + id),
}

export const promptApi = {
  getList: (type) => api.get('/prompts/list', { params: { type } }),
  get: (id) => api.get(`/prompts/${id}`),
  create: (data) => api.post('/prompts/', data),
  update: (id, data) => api.put(`/prompts/${id}`, data),
  delete: (id) => api.delete(`/prompts/${id}`),
  build: (id, data) => api.post(`/prompts/${id}/build`, data),
  import: (data) => api.post('/prompts/import', data),
  exportAll: () => api.get('/prompts/export/all'),
}

export const questionApi = {
  getList: (params) => api.get('/questions/list', { params }),
  get: (id) => api.get(`/questions/${id}`),
  create: (data) => api.post('/questions/', data),
  update: (id, data) => api.put(`/questions/${id}`, data),
  delete: (id) => api.delete(`/questions/${id}`),
  parse: (data) => api.post('/questions/parse', data),
  parseOnly: (data) => api.post('/questions/parse-only', data),
  quickCreate: (data) => api.post('/questions/quick-create', data),
  parseNote: (data) => api.post('/questions/parse-note', data),
  aggregate: (level3, level4) => api.get(`/questions/aggregate/${level3}/${level4}`),
}

export const reviewApi = {
  getDue: (limit) => api.get('/review/due', { params: { limit } }),
  submit: (data) => api.post('/review/submit', data),
  getStats: () => api.get('/review/stats'),
  getLogs: (limit) => api.get('/review/logs', { params: { limit } }),
  getOverdue: () => api.get('/review/overdue'),
}

export const noteApi = {
  getList: (params) => api.get('/notes/list', { params }),
  get: (id) => api.get(`/notes/${id}`),
  fromAi: (data) => api.post('/notes/from-ai', data),
  parseOnly: (data) => api.post('/notes/parse-only', data),
  generateFromQuestion: (data) => api.post('/notes/generate-from-question', data),
  create: (data) => api.post('/notes/', data),
  update: (id, data) => api.put(`/notes/${id}`, data),
  delete: (id) => api.delete(`/notes/${id}`),
}

export const studyApi = {
  getStages: () => api.get('/study/stages'),
  createStage: (data) => api.post('/study/stages', data),
  updateStage: (id, data) => api.put(`/study/stages/${id}`, data),
  deleteStage: (id) => api.delete(`/study/stages/${id}`),
}

export const statsApi = {
  dashboard: () => api.get('/stats/dashboard'),
  radar: () => api.get('/stats/radar'),
  errorDistribution: () => api.get('/stats/error-distribution'),
  trend: (days) => api.get('/stats/trend', { params: { days } }),
  heatmap: (year) => api.get('/stats/heatmap', { params: { year } }),
  weakPoints: (top) => api.get('/stats/weak-points', { params: { top } }),
  recommendation: () => api.get('/stats/recommendation'),
  examCountdown: () => api.get('/stats/exam-countdown'),
  all: () => api.get('/stats/all'),
}

export const examApi = {
  getList: () => api.get('/exam/list'),
  create: (data) => api.post('/exam/', data),
  update: (id, data) => api.put(`/exam/${id}`, data),
  delete: (id) => api.delete(`/exam/${id}`),
}

export const knowledgeApi = {
  getList: (params) => api.get('/knowledge/list', { params }),
  get: (id) => api.get(`/knowledge/${id}`),
  byModule: (module) => api.get(`/knowledge/by-module/${encodeURIComponent(module)}`),
  create: (data) => api.post('/knowledge/', data),
  update: (id, data) => api.put(`/knowledge/${id}`, data),
  delete: (id) => api.delete(`/knowledge/${id}`),
  batch: (items) => api.post('/knowledge/batch', { items }),
}

export const solveLibraryApi = {
  getList: (params) => api.get('/solve-library/list', { params }),
  get: (id) => api.get(`/solve-library/${id}`),
  byModule: (module) => api.get(`/solve-library/by-module/${encodeURIComponent(module)}`),
  create: (data) => api.post('/solve-library/', data),
  update: (id, data) => api.put(`/solve-library/${id}`, data),
  delete: (id) => api.delete(`/solve-library/${id}`),
  batch: (items) => api.post('/solve-library/batch', { items }),
}

export const backupApi = {
  info: () => api.get('/backup/info'),
  create: () => api.post('/backup/create'),
  list: () => api.get('/backup/list'),
  restore: (filename) => api.post('/backup/restore', { filename }),
  delete: (filename) => api.delete('/backup/delete', { params: { filename } }),
  exportAll: () => api.get('/backup/export/all'),
  exportQuestions: () => api.get('/backup/export/questions/md', { responseType: 'blob' }),
  exportNotes: () => api.get('/backup/export/notes/md', { responseType: 'blob' }),
}

export default api
