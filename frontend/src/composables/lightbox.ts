import { reactive } from 'vue'

import { photoUrl } from '@/api'

/** 全局大图灯箱状态：任意组件调用 lightbox.open(path, list?) 查看 ~1600px 高清档；
 * 传 list 时支持 ←/→ 在组内切换（#23）。 */
export const lightbox = reactive({
  src: '',
  show: false,
  list: [] as string[],
  index: -1,
  errored: false,
  open(path: string, list?: string[]) {
    lightbox.list = list ?? []
    lightbox.index = lightbox.list.indexOf(path)
    lightbox.src = photoUrl(path, 'full')
    lightbox.show = true
    lightbox.errored = false
    document.body.style.overflow = 'hidden' // 灯箱开着时锁背景滚动（#23）
  },
  step(delta: 1 | -1) {
    if (!lightbox.list.length) return
    lightbox.index = (lightbox.index + delta + lightbox.list.length) % lightbox.list.length
    lightbox.src = photoUrl(lightbox.list[lightbox.index], 'full')
    lightbox.errored = false
  },
  close() {
    lightbox.show = false
    document.body.style.overflow = ''
  },
})
