<script setup lang="ts">
/** 地图页侧边操作栏：竖排工具按钮（本期仅「还原视野」，设计规范见 .scratch/feature-31-map-toolbar/design.md）。 */
const emit = defineEmits<{ (e: 'reset'): void }>()
</script>

<template>
  <div class="maptb">
    <button class="maptb-btn" aria-label="还原地图视野" title="还原地图视野" @click="emit('reset')">🎯</button>
  </div>
</template>

<style scoped>
.maptb {
  position: fixed;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 40;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.92);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  border-radius: 999px;
  box-shadow: var(--shadow);
}
.maptb-btn {
  pointer-events: auto;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 999px;
  background: transparent;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: 0.18s;
}
@media (hover: hover) {
  .maptb-btn:hover {
    background: var(--bg);
  }
}
.maptb-btn:active {
  transform: scale(0.94);
}
.maptb-btn:focus-visible {
  outline: 2px solid var(--coral-deep);
  outline-offset: 3px;
}
@media (prefers-reduced-motion: reduce) {
  .maptb-btn {
    transition: none;
  }
}
@media (max-width: 640px) {
  .maptb {
    left: 12px;
  }
}
</style>
