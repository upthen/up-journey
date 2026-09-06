<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { lightbox, WHEEL_STEP } from '@/composables/lightbox'

function onKey(e: KeyboardEvent) {
  if (!lightbox.show) return
  if (e.key === 'Escape') lightbox.close()
  if (e.key === 'ArrowLeft') lightbox.step(-1)
  if (e.key === 'ArrowRight') lightbox.step(1)
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))

function onWheel(e: WheelEvent) {
  lightbox.zoomAt(e.deltaY < 0 ? WHEEL_STEP : 1 / WHEEL_STEP, e.clientX, e.clientY)
}
function onDbl(e: MouseEvent) {
  lightbox.toggleZoom(e.clientX, e.clientY)
}

// 拖拽平移：仅放大后生效（1x 时交给翻页/关闭语义）
let lastX = 0
let lastY = 0
function onPointerDown(e: PointerEvent) {
  if (lightbox.scale <= 1 || !e.isPrimary) return
  lightbox.dragging = true
  lastX = e.clientX
  lastY = e.clientY
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}
function onPointerMove(e: PointerEvent) {
  if (!lightbox.dragging) return
  lightbox.panBy(e.clientX - lastX, e.clientY - lastY)
  lastX = e.clientX
  lastY = e.clientY
}
function onPointerUp() {
  lightbox.dragging = false
}
function setImgEl(el: unknown) {
  lightbox.el = (el as HTMLImageElement) ?? null
}
</script>

<template>
  <router-view />
  <div
    v-if="lightbox.show"
    class="lightbox"
    :class="{ 'is-errored': lightbox.errored }"
    @click="lightbox.close()"
    @wheel.prevent="onWheel"
  >
    <button
      v-if="lightbox.list.length > 1"
      class="lb-arrow lb-prev"
      aria-label="上一张"
      @click.stop="lightbox.step(-1)"
    >‹</button>

    <div v-if="!lightbox.errored" :key="lightbox.pageKey" class="lb-stage" @click.stop>
      <img
        :ref="setImgEl"
        :src="lightbox.src"
        alt="照片大图"
        draggable="false"
        :class="{ 'is-zoomed': lightbox.scale > 1, 'is-dragging': lightbox.dragging }"
        :style="{
          transform: `translate(${lightbox.x}px, ${lightbox.y}px) rotate(${lightbox.angle}deg) scale(${lightbox.scale})`,
          transition: lightbox.dragging ? 'none' : 'transform .18s ease',
        }"
        @error="lightbox.errored = true"
        @dblclick.prevent="onDbl"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      />
    </div>
    <p v-else class="lb-fallback" @click.stop>照片加载失败——文件可能已被移出相册</p>

    <button
      v-if="lightbox.list.length > 1"
      class="lb-arrow lb-next"
      aria-label="下一张"
      @click.stop="lightbox.step(1)"
    >›</button>

    <div class="lb-toolbar" @click.stop>
      <button
        aria-label="缩小"
        :disabled="lightbox.errored || lightbox.scale <= 1"
        @click="lightbox.zoomBy(1 / 1.5)"
      >−</button>
      <span v-if="lightbox.list.length > 1" class="lb-count">
        {{ lightbox.index + 1 }} / {{ lightbox.list.length }}
      </span>
      <button
        aria-label="放大"
        :disabled="lightbox.errored"
        @click="lightbox.zoomBy(1.5)"
      >＋</button>
      <button
        class="lb-fit"
        aria-label="适合窗口"
        :disabled="lightbox.errored || lightbox.scale <= 1"
        @click="lightbox.fitToWindow()"
      >⤢</button>
      <button aria-label="旋转 90°" :disabled="lightbox.errored" @click="lightbox.rotate()">⟳</button>
      <button class="lb-close" aria-label="关闭" @click="lightbox.close()">✕</button>
    </div>
  </div>
</template>
