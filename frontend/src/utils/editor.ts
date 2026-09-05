/** WangEditor 自定义「相册插图」按钮：打开相册选图器，插入本应用图片服务的 <img>。 */

import type { IDomEditor, IEditorConfig } from '@wangeditor/editor'
import { Boot } from '@wangeditor/editor'
import { ElMessage } from 'element-plus'

let pickerOpener: (() => void) | null = null

/** 当前组件注入的选图器打开回调（TripEdit 挂载时设置）。 */
export function setAlbumPickerOpener(fn: (() => void) | null) {
  pickerOpener = fn
}

class AlbumImageMenu {
  title = '相册插图'
  iconSvg =
    '<svg viewBox="0 0 1024 1024" width="16" height="16"><path d="M854.6 288.7c6 6 9.4 14.1 9.4 22.6V928c0 17.7-14.3 32-32 32H192c-17.7 0-32-14.3-32-32V96c0-17.7 14.3-32 32-32h424.7c8.5 0 16.7 3.4 22.7 9.4l215.2 215.3zM790.2 326L602 137.8V326h188.2zM320 524h400v64H320v-64zm0 160h300v64H320v-64zM150 550l90-90 60 60-150 150-150-150 60-60 90 90z" transform="scale(0.9) translate(56 0)"/></svg>'
  tag = 'button'

  getValue() {
    return ''
  }
  isActive() {
    return false
  }
  isDisabled() {
    return false
  }
  exec(_editor: IDomEditor) {
    pickerOpener?.()
  }
}

const menuKey = 'albumImage'

let registered = false
export function registerAlbumImageMenu() {
  // 标志挂在 window 上：vite HMR 重跑本模块时 module 级变量会复位，
  // 而 wangEditor 的 Boot 全局注册表不会——重复注册同一 key 会直接抛错打断组件。
  const w = window as unknown as { __albumImageMenuRegistered?: boolean }
  if (registered || w.__albumImageMenuRegistered) return
  Boot.registerMenu({
    key: menuKey,
    factory() {
      return new AlbumImageMenu()
    },
  })
  registered = true
  w.__albumImageMenuRegistered = true
}

export const albumToolbarKeys = ['albumImage']

export const editorConfig = (placeholder: string): Partial<IEditorConfig> => ({
  placeholder,
  MENU_CONF: {},
  // 粘贴图片拦截（#21）：wangEditor 默认把粘贴的截图转 base64 内联进正文——
  // 发布后会被展示端 sanitize 剥掉（图片静默消失），且 LongText 字段急速膨胀。
  // 阻止默认行为，引导走「相册插图」；纯文本/普通富文本粘贴不受影响。
  customPaste: (_editor: IDomEditor, event: ClipboardEvent) => {
    const files = event.clipboardData?.files
    if (files && Array.from(files).some((f) => f.type.startsWith('image/'))) {
      ElMessage.warning('正文不支持直接粘贴图片：请通过工具栏「相册插图」选择')
      return false
    }
    return true
  },
})
