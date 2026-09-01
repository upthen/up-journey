/* @wangeditor/editor-for-vue 的 package.json exports 未指向自带类型，
   这里按其 dist/src/index.d.ts 的形状补一个模块声明（Editor/Toolbar 两个 Vue3 组件）。 */
declare module '@wangeditor/editor-for-vue' {
  import type { DefineComponent } from 'vue'

  export const Editor: DefineComponent<{
    modelValue: string
    defaultConfig: Record<string, unknown>
    mode: 'default' | 'simple'
  }>
  export const Toolbar: DefineComponent<{
    editor: unknown
    defaultConfig: Record<string, unknown>
    mode: 'default' | 'simple'
  }>
}
