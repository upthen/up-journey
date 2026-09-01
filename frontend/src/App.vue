<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { lightbox } from '@/composables/lightbox'

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') lightbox.close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <router-view />
  <div v-if="lightbox.show" class="lightbox" @click="lightbox.close()">
    <img :src="lightbox.src" alt="照片大图" />
  </div>
</template>
