<script setup lang="ts">
/** 地图页侧边操作栏：竖排工具按钮（🎯 还原视野 + 📝 去管理端录入，#32 用户反馈迭代）。
 *  与 NavBall 分工：左上脚印球=前进导航，右下 🎯/📝=地图操作与跳转动作。 */
const emit = defineEmits<{ (e: 'reset'): void }>()
</script>

<template>
  <div class="maptb">
    <button class="maptb-btn" aria-label="还原地图视野" title="还原地图视野" @click="emit('reset')">🎯</button>
    <a
      class="maptb-btn maptb-go"
      href="/admin/trips"
      target="_blank"
      rel="noopener"
      aria-label="去记录"
      title="去记录"
    >📝</a>
  </div>
</template>

<style scoped>
.maptb {
  position: fixed;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 40;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.92);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  border-radius: 999px;
  box-shadow: var(--shadow);
}
.maptb-btn {
  pointer-events: auto;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 999px;
  background: transparent;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: 0.18s;
}
.maptb-btn:hover {
  background: var(--bg);
}
.maptb-btn:active {
  transform: scale(0.94);
}
.maptb-btn:focus-visible {
  outline: 2px solid var(--coral-deep);
  outline-offset: 2px;
}
.maptb-go {
  /* router-link 渲染为 <a>，复位浏览器默认，使其与 .maptb-btn 的 button 外观一致 */
  text-decoration: none;
  color: inherit;
}
@media (prefers-reduced-motion: reduce) {
  .maptb-btn {
    transition: none;
  }
}
@media (max-width: 640px) {
  .maptb {
    right: 12px;
  }
}
</style>
