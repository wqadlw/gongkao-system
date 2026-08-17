<template>
  <div class="gk-skeleton" v-if="loading">
    <div
      v-for="n in lines"
      :key="n"
      class="gk-skeleton__line"
      :style="{ width: (widths[n - 1] || '100%') }"
    ></div>
  </div>
  <slot v-else />
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  lines: { type: Number, default: 3 },
  widths: { type: Array, default: () => [] },
})
</script>
