<template>
  <button
    class="favstar" :class="{ on: isFav, inline: inline }"
    :title="isFav ? '取消收藏' : '收藏'" :aria-pressed="isFav"
    @click.stop="toggle"
  >
    <el-icon><StarFilled v-if="isFav" /><Star v-else /></el-icon>
  </button>
</template>

<script setup>
// 统一收藏星标：乐观翻转 + 失败回滚（favorites 表为唯一事实源）
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { favoritesApi } from '../api'

const props = defineProps({
  objType: { type: String, required: true },   // question/resource/knowledge/solve_item
  objId: { type: Number, required: true },
  initial: { type: Boolean, default: false },
  inline: { type: Boolean, default: false },   // 行内小尺寸模式
})
const emit = defineEmits(['change'])

const isFav = ref(props.initial)
watch(() => props.initial, v => { isFav.value = v })
watch(() => props.objId, () => { isFav.value = props.initial })

async function toggle() {
  const prev = isFav.value
  isFav.value = !prev            // 乐观更新
  try {
    const res = await favoritesApi.toggle({ obj_type: props.objType, obj_id: props.objId })
    isFav.value = res.data.favorited
    emit('change', res.data.favorited)
  } catch {
    isFav.value = prev           // 失败回滚
    ElMessage.error('收藏操作失败')
  }
}
</script>

<style scoped>
.favstar {
  width: 30px; height: 30px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--border-light); background: rgba(255,255,255,0.92);
  color: var(--text-tertiary); cursor: pointer; transition: all 0.15s;
  font-size: 15px; flex-shrink: 0;
}
.favstar:hover { color: var(--warning); transform: scale(1.1); }
.favstar.on { color: var(--warning); border-color: var(--warning-bg); background: var(--warning-bg); }
.favstar.inline { width: 26px; height: 26px; font-size: 13px; border: none; background: transparent; }
</style>
