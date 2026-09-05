import { reactive } from 'vue'

import { photoUrl } from '@/api'

/** 全局大图灯箱状态：任意组件调用 lightbox.open(path) 查看 ~1600px 高清档。 */
export const lightbox = reactive({
  src: '',
  show: false,
  open(path: string) {
    lightbox.src = photoUrl(path, 'full')
    lightbox.show = true
    document.body.style.overflow = 'hidden' // 灯箱开着时锁背景滚动（#23）
  },
  close() {
    lightbox.show = false
    document.body.style.overflow = ''
  },
})
