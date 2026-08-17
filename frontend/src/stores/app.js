import { defineStore } from 'pinia'
import { ref } from 'vue'
import { categoryApi, examApi } from '../api'

export const useAppStore = defineStore('app', () => {
  const darkMode = ref(localStorage.getItem('gk_darkMode') === 'true')
  const categoryTree = ref([])   // 题型树（嵌套）
  const categoryFlat = ref([])   // 题型树（扁平，便于查找）
  const examCountdowns = ref([])
  const isTreeCollapsed = ref(localStorage.getItem('gk_treeCollapsed') === 'true')
  const isSidebarCollapsed = ref(localStorage.getItem('gk_sidebar') === 'true')

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    localStorage.setItem('gk_darkMode', darkMode.value)
    document.body.classList.toggle('dark-theme', darkMode.value)
  }

  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
    localStorage.setItem('gk_sidebar', isSidebarCollapsed.value)
  }

  function toggleTree() {
    isTreeCollapsed.value = !isTreeCollapsed.value
    localStorage.setItem('gk_treeCollapsed', isTreeCollapsed.value)
  }

  function initTheme() {
    document.body.classList.toggle('dark-theme', darkMode.value)
  }

  async function loadCategories() {
    try {
      const [treeRes, listRes] = await Promise.all([
        categoryApi.getTree(),
        categoryApi.getList(),
      ])
      categoryTree.value = treeRes.data
      categoryFlat.value = listRes.data
    } catch (e) {
      console.error('加载分类树失败', e)
    }
  }

  async function loadExamCountdowns() {
    try {
      const res = await examApi.getList()
      examCountdowns.value = res.data
    } catch (e) {
      console.error('加载倒计时失败', e)
    }
  }

  function findCategory(id) {
    return categoryFlat.value.find(c => c.id === Number(id)) || null
  }

  return {
    darkMode, categoryTree, categoryFlat, examCountdowns, isTreeCollapsed, isSidebarCollapsed,
    toggleDarkMode, toggleTree, toggleSidebar, initTheme,
    loadCategories, loadExamCountdowns, findCategory,
  }
})
