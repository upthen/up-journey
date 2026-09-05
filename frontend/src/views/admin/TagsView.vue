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

const error = ref(false)

async function load() {
  loading.value = true
  error.value = false
  try {
    tags.value = await api.admin.tags()
  } catch {
    error.value = true
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
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 409) {
      ElMessage.error('添加失败：标签已存在')
    } else if (err.response?.data?.detail) {
      ElMessage.error(`添加失败：${err.response.data.detail}`)
    } else {
      ElMessage.error('添加失败，请稍后重试')
    }
  }
}

async function rename(t: Tag) {
  let value: string
  try {
    ;({ value } = await ElMessageBox.prompt('新的标签名（1-16 个字符）', '重命名', {
      inputValue: t.name,
      // 列表页输入框有 maxlength=16，弹窗此前没有——超长会被后端 422 且报错文案误导（#19）
      inputPattern: /^.{1,16}$/,
      inputErrorMessage: '标签名需 1-16 个字符',
    }))
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
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 409) {
      ElMessage.error('重命名失败：标签名已被占用')
    } else if (err.response?.data?.detail) {
      ElMessage.error(`重命名失败：${err.response.data.detail}`)
    } else {
      ElMessage.error('重命名失败，请稍后重试')
    }
  }
}

async function remove(t: Tag) {
  try {
    await ElMessageBox.confirm(`删除标签「${t.name}」？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    await api.admin.deleteTag(t.id)
  } catch {
    ElMessage.error('删除失败，请稍后重试')
    return
  }
  ElMessage.success('已删除')
  await load()
  meta.refresh()
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="ad-error-bar">
      <span>标签列表加载失败——网络或服务暂时不可用。</span>
      <el-button size="small" @click="load">重 试</el-button>
    </div>
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
