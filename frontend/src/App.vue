<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import BackHome from '@/components/BackHome.vue'
import { lightbox, MIN_SCALE, WHEEL_STEP } from '@/composables/lightbox'

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

// 拖拽平移（鼠标）：仅放大后生效（1x 时交给翻页/关闭语义）；触摸由 touch 手势接管
let lastX = 0
let lastY = 0
function onPointerDown(e: PointerEvent) {
  if (e.pointerType !== 'mouse' || lightbox.scale <= MIN_SCALE || !e.isPrimary) return
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

// —— 触摸手势：1x 横滑翻页（不足回弹）/ 放大后单指平移 / 双指捏合缩放 / 双击点按 ——
const SWIPE_PX = 48
const TAP_MS = 320
let touchMode: null | 'swipe' | 'pan' | 'pinch' = null
let startX = 0
let startY = 0
let movedFar = false
let lastTouchX = 0
let lastTouchY = 0
let lastDist = 0
let lastTapAt = 0
let lastTapX = 0
let lastTapY = 0
let suppressClick = false

function onTouchStart(e: TouchEvent) {
  suppressClick = false // 新手势开始：此前滑动遗留的 click 豁免作废
  if (e.touches.length === 1) {
    const t = e.touches[0]
    touchMode = lightbox.scale > MIN_SCALE ? 'pan' : 'swipe'
    startX = lastTouchX = t.clientX
    startY = lastTouchY = t.clientY
    movedFar = false
  } else if (e.touches.length >= 2) {
    touchMode = 'pinch'
    const [a, b] = [e.touches[0], e.touches[1]]
    lastDist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
    lastTouchX = (a.clientX + b.clientX) / 2
    lastTouchY = (a.clientY + b.clientY) / 2
  }
}
function onTouchMove(e: TouchEvent) {
  if (!touchMode) return
  e.preventDefault()
  if (touchMode === 'pan' && e.touches.length === 1) {
    const t = e.touches[0]
    lightbox.panBy(t.clientX - lastTouchX, t.clientY - lastTouchY)
    lastTouchX = t.clientX
    lastTouchY = t.clientY
  } else if (touchMode === 'pinch' && e.touches.length >= 2) {
    const [a, b] = [e.touches[0], e.touches[1]]
    const dist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
    const cx = (a.clientX + b.clientX) / 2
    const cy = (a.clientY + b.clientY) / 2
    if (lastDist > 0) lightbox.zoomAt(dist / lastDist, cx, cy)
    lightbox.panBy(cx - lastTouchX, cy - lastTouchY)
    lastDist = dist
    lastTouchX = cx
    lastTouchY = cy
  } else if (touchMode === 'swipe') {
    const t = e.touches[0]
    lastTouchX = t.clientX
    lastTouchY = t.clientY
    if (Math.hypot(t.clientX - startX, t.clientY - startY) > 12) movedFar = true
  }
}
function onTouchEnd(e: TouchEvent) {
  if ((touchMode === 'swipe' || touchMode === 'pan') && e.touches.length === 0) {
    const dx = lastTouchX - startX
    const dy = lastTouchY - startY
    if (!movedFar) {
      // 点按（≤12px）：双击点按在适合窗口 ↔ 2x 间切换（放大态下点按也归位）
      const now = Date.now()
      if (now - lastTapAt < TAP_MS && Math.hypot(lastTouchX - lastTapX, lastTouchY - lastTapY) < 28) {
        lightbox.toggleZoom(lastTouchX, lastTouchY)
        lastTapAt = 0
      } else {
        lastTapAt = now
        lastTapX = lastTouchX
        lastTapY = lastTouchY
      }
    } else if (touchMode === 'swipe' && Math.abs(dx) > SWIPE_PX && Math.abs(dx) > Math.abs(dy) * 1.2) {
      // 横滑超阈值翻页；放大态只平移不翻页
      suppressClick = true // 吃掉滑动后合成的 click，避免误关灯箱
      lightbox.step(dx < 0 ? 1 : -1)
      lastTapAt = 0 // 翻页后重置双击计时，避免连滑被误判
    } else if (touchMode === 'swipe') {
      // 轻拨/纵向滑动：轻推一下弹回，明示"不翻页"
      const nx = Math.max(-14, Math.min(14, dx * 0.12))
      const ny = Math.max(-14, Math.min(14, dy * 0.12))
      if (nx || ny) lightbox.nudge(nx, ny)
    }
  }
  if (e.touches.length === 0) touchMode = null
  else if (e.touches.length === 1 && touchMode === 'pinch') {
    touchMode = 'pan'
    lastTouchX = e.touches[0].clientX
    lastTouchY = e.touches[0].clientY
  }
}
function onOverlayClick() {
  if (suppressClick) {
    suppressClick = false
    return
  }
  lightbox.close()
}
</script>

<template>
  <router-view />
  <BackHome />
  <div
    v-if="lightbox.show"
    class="lightbox"
    :class="{ 'is-errored': lightbox.errored }"
    role="dialog"
    aria-modal="true"
    aria-label="照片查看器"
    @click="onOverlayClick"
    @wheel.prevent="onWheel"
    @touchstart="onTouchStart"
    @touchmove.prevent="onTouchMove"
    @touchend="onTouchEnd"
    @touchcancel="onTouchEnd"
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
        :class="{ 'is-zoomed': lightbox.scale > MIN_SCALE, 'is-dragging': lightbox.dragging }"
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
        :disabled="lightbox.errored || lightbox.scale <= MIN_SCALE"
        @click="lightbox.zoomAt(1 / 1.5)"
      >−</button>
      <span v-if="lightbox.list.length > 1" class="lb-count">
        {{ lightbox.index + 1 }} / {{ lightbox.list.length }}
      </span>
      <button
        aria-label="放大"
        :disabled="lightbox.errored"
        @click="lightbox.zoomAt(1.5)"
      >＋</button>
      <button
        class="lb-fit"
        aria-label="适合窗口"
        :disabled="lightbox.errored || lightbox.scale <= MIN_SCALE"
        @click="lightbox.fitToWindow()"
      >⤢</button>
      <button aria-label="旋转 90°" :disabled="lightbox.errored" @click="lightbox.rotate()">⟳</button>
      <button class="lb-close" aria-label="关闭" @click="lightbox.close()">✕</button>
    </div>
  </div>
</template>
