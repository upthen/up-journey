import { reactive } from 'vue'

import { photoUrl } from '@/api'

/** 全局大图灯箱：任意组件调用 lightbox.open(path, list?) 查看 ~2600px 高清档；
 * 传 list 时支持 ←/→ 与侧箭头在组内切换。查看器能力（缩放/平移/旋转）状态也在此单例内。 */
const MIN_SCALE = 1
const MAX_SCALE = 4
const WHEEL_STEP = 1.2
const DBLCLICK_SCALE = 2
const TOOLBAR_STEP = 1.5

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

export const lightbox = reactive({
  src: '',
  show: false,
  list: [] as string[],
  index: -1,
  errored: false,
  // 视图变换：1x = 适合窗口（CSS 约束最大宽高）；平移偏移按屏幕轴（旋转后拖拽方向不变）
  scale: 1,
  x: 0,
  y: 0,
  angle: 0, // 90° 步进，纯查看辅助，不落库
  pageKey: 0, // 每次换图自增，触发入场过渡
  dragging: false,
  el: null as HTMLImageElement | null, // 当前 <img>，用于以光标为锚缩放和平移钳制

  open(path: string, list?: string[]) {
    lightbox.list = list ?? []
    lightbox.index = lightbox.list.indexOf(path)
    lightbox.src = photoUrl(path, 'full')
    lightbox.errored = false
    lightbox._resetView()
    lightbox.pageKey++
    lightbox.show = true
    document.body.style.overflow = 'hidden' // 灯箱开着时锁背景滚动（#23）
  },
  step(delta: 1 | -1) {
    if (!lightbox.list.length) return
    lightbox.index = (lightbox.index + delta + lightbox.list.length) % lightbox.list.length
    lightbox.src = photoUrl(lightbox.list[lightbox.index], 'full')
    lightbox.errored = false
    lightbox._resetView()
    lightbox.pageKey++
  },
  close() {
    lightbox.show = false
    document.body.style.overflow = ''
  },

  /** 滚轮/按钮缩放：桌面滚轮以光标为锚（仅未旋转时，旋转后以中心为锚）。 */
  zoomAt(factor: number, cx?: number, cy?: number) {
    const el = lightbox.el
    if (!el) return
    const from = lightbox.scale
    const to = clamp(from * factor, MIN_SCALE, MAX_SCALE)
    if (to === from) return
    if (cx != null && cy != null && lightbox.angle % 360 === 0) {
      const r = el.getBoundingClientRect()
      const centerX = r.left + r.width / 2
      const centerY = r.top + r.height / 2
      lightbox.x += (1 - to / from) * (cx - centerX)
      lightbox.y += (1 - to / from) * (cy - centerY)
    }
    lightbox.scale = to
    lightbox._clampPan()
  },
  zoomBy(factor: number) {
    lightbox.zoomAt(factor)
  },
  /** 双击/双击点按：适合窗口 ↔ 2x（以点击处为锚）。 */
  toggleZoom(cx?: number, cy?: number) {
    if (lightbox.scale > MIN_SCALE) lightbox.fitToWindow()
    else lightbox.zoomAt(DBLCLICK_SCALE / lightbox.scale, cx, cy)
  },
  /** 适合窗口：复位缩放与平移，保留旋转（旋转是观看者主动的选择）。 */
  fitToWindow() {
    lightbox.scale = 1
    lightbox.x = 0
    lightbox.y = 0
  },
  rotate() {
    lightbox.angle = (lightbox.angle + 90) % 360
    lightbox._clampPan()
  },

  // —— 内部 ——
  _resetView() {
    lightbox.scale = 1
    lightbox.x = 0
    lightbox.y = 0
    lightbox.angle = 0
  },
  /** 适合窗口下的图片显示尺寸（旋转 90/270 时宽高互换）。 */
  _fitDims(): { w: number; h: number } | null {
    const el = lightbox.el
    if (!el) return null
    const r = el.getBoundingClientRect()
    if (!r.width || !r.height) return null
    const swapped = lightbox.angle % 180 !== 0
    return {
      w: (swapped ? r.height : r.width) / lightbox.scale,
      h: (swapped ? r.width : r.height) / lightbox.scale,
    }
  },
  /** 平移钳制：放大后图片任何一边不得脱离可视区。 */
  _clampPan() {
    const dims = lightbox._fitDims()
    if (!dims || lightbox.scale <= MIN_SCALE) {
      lightbox.x = 0
      lightbox.y = 0
      return
    }
    const maxX = (dims.w * lightbox.scale - dims.w) / 2
    const maxY = (dims.h * lightbox.scale - dims.h) / 2
    lightbox.x = clamp(lightbox.x, -maxX, maxX)
    lightbox.y = clamp(lightbox.y, -maxY, maxY)
  },
  panBy(dx: number, dy: number) {
    if (lightbox.scale <= MIN_SCALE) return
    lightbox.x += dx
    lightbox.y += dy
    lightbox._clampPan()
  },
})

export { MIN_SCALE, MAX_SCALE, WHEEL_STEP, TOOLBAR_STEP }
