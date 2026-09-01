<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api } from '@/api'
import { useMetaStore } from '@/stores/meta'
import type { Member } from '@/types'

const meta = useMetaStore()
const members = ref<Member[]>([])
const loading = ref(false)

const dialog = ref(false)
const editing = ref<Member | null>(null)
const form = ref({ name: '', nickname: '', is_child: false })

async function load() {
  loading.value = true
  try {
    members.value = await api.admin.members()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', nickname: '', is_child: false }
  dialog.value = true
}
function openEdit(m: Member) {
  editing.value = m
  form.value = { name: m.name, nickname: m.nickname || '', is_child: m.is_child }
  dialog.value = true
}

async function save() {
  if (!form.value.name.trim()) {
    ElMessage.warning('姓名必填')
    return
  }
  const payload = {
    name: form.value.name.trim(),
    nickname: form.value.nickname.trim() || undefined,
    is_child: form.value.is_child,
  }
  try {
    if (editing.value) {
      await api.admin.updateMember(editing.value.id, payload)
    } else {
      await api.admin.createMember(payload)
    }
    dialog.value = false
    ElMessage.success('已保存')
    await load()
    meta.refresh()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '保存失败')
  }
}

async function remove(m: Member) {
  try {
    await ElMessageBox.confirm(`删除成员「${m.nickname || m.name}」？其与旅行的关联会一并解除。`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  await api.admin.deleteMember(m.id)
  ElMessage.success('已删除')
  await load()
  meta.refresh()
}

onMounted(load)
</script>

<template>
  <div>
    <section class="ad-panel">
      <h4>家庭成员</h4>
      <p class="hint">称呼用于展示端头像与同行列表；勾选"孩子"后，含该成员的旅行计入"带娃出行"统计。</p>
      <div class="flex justify-between items-center mb-3">
        <span class="text-sm text-gray-400">共 {{ members.length }} 位成员</span>
        <el-button type="primary" @click="openCreate">＋ 新增成员</el-button>
      </div>
      <el-table v-loading="loading" :data="members" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="180" />
        <el-table-column prop="nickname" label="称呼">
          <template #default="{ row }">{{ row.nickname || '—' }}</template>
        </el-table-column>
        <el-table-column label="孩子" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_child" type="danger" size="small">孩子</el-tag>
            <span v-else class="text-gray-300">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialog" :title="editing ? '编辑成员' : '新增成员'" width="420px">
      <el-form label-width="72px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" maxlength="32" placeholder="如 张三" />
        </el-form-item>
        <el-form-item label="称呼">
          <el-input v-model="form.nickname" maxlength="32" placeholder="如 爸爸 / 妈妈 / 哥哥" />
        </el-form-item>
        <el-form-item label="是否孩子">
          <el-switch v-model="form.is_child" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
