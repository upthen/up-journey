import { reactive } from 'vue'

import { photoUrl } from '@/api'

/** 全局大图灯箱状态：任意组件调用 lightbox.open(path) 查看 ~1600px 高清档。 */
export const lightbox = reactive({
  src: '',
  show: false,
  open(path: string) {
    lightbox.src = photoUrl(path, 'full')
    lightbox.show = true
  },
  close() {
    lightbox.show = false
  },
})
