<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { lightbox } from '@/composables/lightbox'

function onKey(e: KeyboardEvent) {
  if (!lightbox.show) return
  if (e.key === 'Escape') lightbox.close()
  if (e.key === 'ArrowLeft') lightbox.step(-1)
  if (e.key === 'ArrowRight') lightbox.step(1)
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <router-view />
  <div v-if="lightbox.show" class="lightbox" @click="lightbox.close()">
    <img v-if="!lightbox.errored" :src="lightbox.src" alt="照片大图" @error="lightbox.errored = true" />
    <p v-else class="lb-fallback">照片加载失败——文件可能已被移出相册</p>
  </div>
</template>
