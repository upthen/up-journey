<script setup lang="ts">
/** NAS 共享相册浏览器（只读）：供选封面、配景点相册目录、游记插图。 */
import { Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref, watch } from 'vue'

import { api, photoUrl } from '@/api'
import type { Album } from '@/types'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    initialPath?: string
    mode?: 'photo' | 'dir' // 选图片 or 选目录
    title?: string
  }>(),
  { initialPath: '', mode: 'photo', title: '从相册选择' },
)
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'select', payload: { path: string; name: string }): void
}>()

const album = ref<Album | null>(null)
const loading = ref(false)

const crumbs = computed(() => {
  const cur = album.value?.current ?? ''
  if (!cur) return []
  const parts = cur.split('/')
  return parts.map((name, i) => ({ name, path: parts.slice(0, i + 1).join('/') }))
})

async function open(path = '') {
  loading.value = true
  try {
    album.value = await api.admin.album(path)
  } catch (e) {
    ElMessage.error('打开目录失败')
    album.value = null
  } finally {
    loading.value = false
  }
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) open(props.initialPath)
  },
)

function pickPhoto(p: string) {
  if (props.mode !== 'photo') return
  emit('select', { path: p, name: p.split('/').pop() || p })
  emit('update:modelValue', false)
}
function pickDir(p: string) {
  if (props.mode === 'dir') {
    emit('select', { path: p, name: p.split('/').pop() || p })
    emit('update:modelValue', false)
  } else {
    open(p)
  }
}
function chooseCurrentDir() {
  // dir 模式允许直接选中当前目录（景点相册根）
  const cur = album.value?.current ?? ''
  emit('select', { path: cur, name: cur.split('/').pop() || '相册根目录' })
  emit('update:modelValue', false)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    width="760px"
    top="6vh"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-loading="loading" class="album-browser">
      <div class="crumbs">
        <button @click="open('')">🏠 相册根</button>
        <template v-for="c in crumbs" :key="c.path">
          <span>›</span>
          <button @click="open(c.path)">{{ c.name }}</button>
        </template>
        <span v-if="album?.parent !== null || album?.current" class="flex-1"></span>
        <button v-if="album?.parent" @click="open(album.parent)">← 上一级</button>
      </div>

      <div v-if="album && !album.dirs.length && !album.photos.length" class="text-center text-gray-400 py-10">
        这个目录是空的
      </div>
      <div v-else class="entries">
        <div
          v-for="d in album?.dirs ?? []"
          :key="d.path"
          class="entry dir"
          :title="mode === 'dir' ? '点击选择此目录' : '进入目录'"
          @click="pickDir(d.path)"
        >
          <el-icon :size="26"><Folder /></el-icon>
          <span>{{ d.name }}</span>
        </div>
        <div
          v-for="p in album?.photos ?? []"
          :key="p"
          class="entry pic"
          :class="{ 'opacity-40 pointer-events-none': mode === 'dir' }"
          :title="mode === 'dir' ? '' : '点击选择'"
          @click="pickPhoto(p)"
        >
          <img :src="photoUrl(p, 'thumb')" loading="lazy" :alt="p" />
        </div>
      </div>
    </div>
    <template v-if="mode === 'dir'" #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="chooseCurrentDir">选用当前目录{{ album?.current ? `（${album.current}）` : '（相册根）' }}</el-button>
    </template>
  </el-dialog>
</template>
