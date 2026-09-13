<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import BackHome from '@/components/BackHome.vue'
import { lightbox } from '@/composables/lightbox'

function onKey(e: KeyboardEvent) {
  if (!lightbox.show) return
  if (e.key === 'Escape') lightbox.close()
  if (e.key === 'ArrowLeft') lightbox.step(-1)
  if (e.key === 'ArrowRight') lightbox.step(1)
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))

// 触屏滑动翻页（#37）：横向位移 >40px 判定一次翻页，点按仍走整层关闭
let touchX = 0
function onTouchStart(e: TouchEvent) {
  touchX = e.touches[0]?.clientX ?? 0
}
function onTouchEnd(e: TouchEvent) {
  if (!lightbox.show || !lightbox.list.length) return
  const dx = (e.changedTouches[0]?.clientX ?? 0) - touchX
  if (Math.abs(dx) > 40) lightbox.step(dx < 0 ? 1 : -1)
}
</script>

<template>
  <router-view />
  <BackHome />
  <div
    v-if="lightbox.show"
    class="lightbox"
    role="dialog"
    aria-modal="true"
    aria-label="照片查看器"
    @click="lightbox.close()"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
  >
    <img v-if="!lightbox.errored" :src="lightbox.src" alt="照片大图" @error="lightbox.errored = true" />
    <p v-else class="lb-fallback">照片加载失败——文件可能已被移出相册</p>
    <!-- 控件条（#37）：关闭/翻页/计数在所有端可见；点控件不冒泡关闭 -->
    <button v-if="lightbox.list.length > 1" class="lb-nav lb-prev" aria-label="上一张" @click.stop="lightbox.step(-1)">‹</button>
    <button v-if="lightbox.list.length > 1" class="lb-nav lb-next" aria-label="下一张" @click.stop="lightbox.step(1)">›</button>
    <p v-if="lightbox.list.length > 1" class="lb-count">{{ lightbox.index + 1 }} / {{ lightbox.list.length }}</p>
    <button class="lb-close" aria-label="关闭" @click.stop="lightbox.close()">✕</button>
  </div>
</template>
