<script setup lang="ts">
/** 右下角「回家」胶囊：非地图页常驻返回键。
 *  与 NavBall 分工：左上珊瑚球=前进导航（展开菜单），右下墨色胶囊=单击回 `/`。
 *  设计规范见 .scratch/back-button-redesign/design.md。 */
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const show = computed(() => route.path !== '/' && !route.path.startsWith('/admin'))
</script>

<template>
  <router-link v-if="show" class="back-home" to="/">
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
  transition: background 0.18s, transform 0.18s, box-shadow 0.18s;
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
