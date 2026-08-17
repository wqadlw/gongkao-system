<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"
             title="⌨️ 键盘快捷键" width="460px" align-center>
    <div class="sc-list">
      <div class="sc-row" v-for="s in SHORTCUTS" :key="s.key">
        <kbd class="sc-key">{{ s.key === '?' ? '?' : s.key.toUpperCase() }}</kbd>
        <span class="sc-desc">{{ s.desc }}</span>
        <span class="sc-path" v-if="s.path">{{ s.path }}</span>
      </div>
    </div>
    <p class="sc-tip">提示：在任意输入框中按键不会触发快捷键；按 <kbd>?</kbd> 随时呼出本帮助。</p>
  </el-dialog>
</template>

<script setup>
import { SHORTCUTS } from '../composables/useShortcuts'

defineProps({ modelValue: { type: Boolean, default: false } })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.sc-list { display: flex; flex-direction: column; gap: 2px; }
.sc-row {
  display: flex; align-items: center; gap: 12px;
  padding: 7px 6px; border-radius: 8px;
}
.sc-row:nth-child(odd) { background: var(--bg-subtle); }
.sc-key {
  flex-shrink: 0; min-width: 30px; text-align: center;
  font-family: 'Consolas', monospace; font-size: 12px; font-weight: 700;
  background: var(--bg-elevated); border: 1px solid var(--border-base);
  border-bottom-width: 2px; border-radius: 6px; padding: 3px 8px;
  color: var(--text-primary);
}
.sc-desc { flex: 1; font-size: 13.5px; color: var(--text-primary); }
.sc-path { font-size: 11.5px; color: var(--text-tertiary); font-family: 'Consolas', monospace; }
.sc-tip { margin: 14px 0 0; font-size: 12px; color: var(--text-tertiary); line-height: 1.6; }
.sc-tip kbd {
  font-family: 'Consolas', monospace; font-size: 11px;
  background: var(--bg-elevated); border: 1px solid var(--border-base);
  border-radius: 4px; padding: 1px 6px;
}
</style>
