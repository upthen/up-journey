<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api } from '@/api'
import { useMetaStore } from '@/stores/meta'
import type { Tag } from '@/types'

const meta = useMetaStore()
const tags = ref<Tag[]>([])
const loading = ref(false)
const newName = ref('')

async function load() {
  loading.value = true
  try {
    tags.value = await api.admin.tags()
  } finally {
    loading.value = false
  }
}

async function add() {
  const name = newName.value.trim()
  if (!name) return
  try {
    await api.admin.createTag(name)
    newName.value = ''
    ElMessage.success('已添加')
    await load()
    meta.refresh()
  } catch {
    ElMessage.error('添加失败：标签可能已存在')
  }
}

async function rename(t: Tag) {
  let value: string
  try {
    ;({ value } = await ElMessageBox.prompt('新的标签名', '重命名', { inputValue: t.name }))
  } catch {
    return // 用户取消
  }
  const name = value.trim()
  if (!name || name === t.name) return
  try {
    await api.admin.updateTag(t.id, name)
    ElMessage.success('已保存')
    await load()
    meta.refresh()
  } catch {
    ElMessage.error('重命名失败：可能与其他标签重名')
  }
}

async function remove(t: Tag) {
  try {
    await ElMessageBox.confirm(`删除标签「${t.name}」？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  await api.admin.deleteTag(t.id)
  ElMessage.success('已删除')
  await load()
  meta.refresh()
}

onMounted(load)
</script>

<template>
  <div>
    <section class="ad-panel">
      <h4>标签管理</h4>
      <p class="hint">标签字典供录入旅行时勾选，如 亲子 / 自驾 / 海岛 / 高原。</p>
      <div class="flex gap-2 mb-4">
        <el-input v-model="newName" maxlength="16" placeholder="新标签名（回车添加）" style="max-width: 240px" @keydown.enter="add" />
        <el-button type="primary" @click="add">添加</el-button>
      </div>
      <el-table v-loading="loading" :data="tags" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="标签" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="rename(row)">重命名</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
