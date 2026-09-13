<script setup lang="ts">
/** 右下角「回家」胶囊：非地图页常驻返回键。
 *  与 NavBall 分工：左上珊瑚球=前进导航（展开菜单），右下墨色胶囊=单击回 `/`。
 *  设计规范见 .scratch/back-button-redesign/design.md。 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const show = computed(() => route.path !== '/' && !route.path.startsWith('/admin'))

/* 下滑阅读时收起、上滑即回（#38）。
 * 仅窄屏生效——桌面端胶囊悬浮在双列布局留白上，不遮正文，保持规范 §2.6 的「恒定可见」。 */
const compactMq = window.matchMedia('(max-width: 640px)')
const hidden = ref(false)
let lastY = 0
function onScroll() {
  const y = window.scrollY
  if (!compactMq.matches) {
    hidden.value = false
  } else {
    hidden.value = y > lastY + 4 && y > 80 // 位移太小不抖动；页顶附近恒显
  }
  lastY = y
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <router-link v-if="show" class="back-home" :class="{ 'is-hidden': hidden }" to="/">
    <span class="arr" aria-hidden="true">←</span> 回到地图
  </router-link>
</template>

<style scoped>
.back-home {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 55;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  padding: 0 20px;
  border-radius: 999px;
  background: var(--ink);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  box-shadow: var(--shadow-lg);
  animation: bh-in 0.28s cubic-bezier(0.22, 1, 0.36, 1);
  transition: background 0.18s, transform 0.18s, box-shadow 0.18s, opacity 0.22s;
}
.back-home.is-hidden {
  opacity: 0;
  pointer-events: none; /* 隐藏态不吃触点，防止误触 */
  transform: translateY(8px);
}
.back-home .arr {
  color: var(--coral);
  font-weight: 700;
}
@media (hover: hover) {
  .back-home:hover {
    background: var(--coral);
  }
}
.back-home:active {
  transform: scale(0.96);
}
.back-home:focus-visible {
  outline: 2px solid var(--coral-deep);
  outline-offset: 3px;
}
@keyframes bh-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .back-home {
    animation: none;
    transition: none;
  }
}
@media (max-width: 640px) {
  .back-home {
    right: 12px;
    bottom: calc(16px + env(safe-area-inset-bottom));
  }
}
</style>
