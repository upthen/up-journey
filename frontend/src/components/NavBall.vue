<script setup lang="ts">
/** 展示端悬浮导航：左上角吸边小球，点击展开贴边胶囊菜单（设计规范见 .scratch/feature-30-nav-ball/design.md）。 */
import { onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

defineProps<{ active: 'map' | 'timeline' | 'list' }>()

const route = useRoute()
const open = ref(false)
const ballEl = ref<HTMLButtonElement>()

// 路由切换即收起（点击链接跳转 / 外部直达均保持收起态）
watch(
  () => route.path,
  () => (open.value = false),
)

function onDocClick(e: MouseEvent) {
  if (!open.value) return
  const t = e.target as HTMLElement
  if (t.closest('.nb')) return
  open.value = false
}
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && open.value) {
    open.value = false
    ballEl.value?.focus()
  }
}
window.addEventListener('click', onDocClick)
window.addEventListener('keydown', onKeydown)
onUnmounted(() => {
  window.removeEventListener('click', onDocClick)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <nav class="nb" aria-label="主导航">
    <button
      ref="ballEl"
      class="nb-ball"
      :aria-expanded="open"
      aria-controls="nb-menu"
      aria-label="导航菜单"
      title="导航菜单"
      @click="open = !open"
    >
      🧭
    </button>
    <div id="nb-menu" class="nb-menu" :class="{ open }">
      <router-link to="/" :class="{ active: active === 'map' }" :aria-current="active === 'map' ? 'page' : undefined">地图</router-link>
      <router-link to="/timeline" :class="{ active: active === 'timeline' }" :aria-current="active === 'timeline' ? 'page' : undefined">编年</router-link>
      <router-link to="/list" :class="{ active: active === 'list' }" :aria-current="active === 'list' ? 'page' : undefined">游记名录</router-link>
      <span class="nb-sep" aria-hidden="true"></span>
      <span class="nb-brand">游迹</span>
    </div>
  </nav>
</template>

<style scoped>
.nb {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 60;
  pointer-events: none;
}
.nb-ball,
.nb-menu {
  pointer-events: auto;
}
.nb-ball {
  position: relative;
  z-index: 2;
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 50%;
  background: var(--coral);
  color: #fff;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: 0.18s;
}
@media (hover: hover) {
  .nb-ball:hover {
    transform: translateY(-1px) scale(1.05);
    box-shadow: var(--shadow-lg);
  }
}
.nb-ball:focus-visible {
  outline: 2px solid var(--coral-deep);
  outline-offset: 3px;
}
.nb-menu {
  position: absolute;
  top: 0;
  left: 0;
  height: 48px;
  padding: 6px 14px 6px 60px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.92);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
  border-radius: 999px;
  box-shadow: var(--shadow);
  opacity: 0;
  visibility: hidden;
  transform: translateX(-8px) scale(0.96);
  transform-origin: left center;
  transition: 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.nb-menu.open {
  opacity: 1;
  visibility: visible;
  transform: none;
  transition: 0.24s cubic-bezier(0.22, 1, 0.36, 1);
}
.nb-menu a {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-2);
  padding: 8px 16px;
  border-radius: 999px;
  transition: 0.18s;
  white-space: nowrap;
}
.nb-menu a:hover {
  background: var(--bg);
}
.nb-menu a.active {
  background: var(--ink);
  color: #fff;
}
.nb-menu a:focus-visible {
  outline: 2px solid var(--coral-deep);
  outline-offset: -2px;
}
.nb-sep {
  width: 1px;
  height: 18px;
  background: var(--hairline);
  margin: 0 4px;
}
.nb-brand {
  font-size: 12px;
  color: var(--gray);
  letter-spacing: 0.2em;
  white-space: nowrap;
}
@media (max-width: 640px) {
  .nb {
    top: 12px;
    left: 12px;
  }
  .nb-menu {
    max-width: calc(100vw - 24px);
  }
  .nb-menu a {
    font-size: 13.5px;
    padding: 8px 12px;
  }
  .nb-sep,
  .nb-brand {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .nb-ball,
  .nb-menu {
    transition: none;
  }
}
</style>
