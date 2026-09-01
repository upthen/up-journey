<script setup lang="ts">
/** 旅行管理列表：按年份/标签/状态/关键词筛选（user story 13），编辑/删除（story 12）。 */
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, photoUrl } from '@/api'
import { useMetaStore } from '@/stores/meta'
import type { TripCard } from '@/types'
import { dateRange } from '@/utils/format'

const router = useRouter()
const meta = useMetaStore()
const trips = ref<TripCard[]>([])
const loading = ref(false)

const filters = ref<{ year: number | null; tag: string; status: string; q: string }>({
  year: null,
  tag: '',
  status: '',
  q: '',
})
const years = computed(() => [...new Set(trips.value.map((t) => t.year))].sort((a, b) => b - a))

async function load() {
  loading.value = true
  try {
    trips.value = await api.admin.trips({
      year: filters.value.year ?? undefined,
      tag: filters.value.tag || undefined,
      status: filters.value.status || undefined,
      q: filters.value.q || undefined,
    })
  } finally {
    loading.value = false
  }
}

async function remove(t: TripCard) {
  try {
    await ElMessageBox.confirm(`删除旅行「${t.title}」？其城市、景点、按天行程会一并删除。`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  await api.admin.deleteTrip(t.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(async () => {
  await meta.ensure()
  await load()
})
</script>

<template>
  <div>
    <section class="ad-panel">
      <h4>旅行管理</h4>
      <p class="hint">草稿不会出现在展示端；发布后地图、编年、名录即时更新。</p>
      <div class="flex flex-wrap gap-2 items-center mb-3">
        <el-select v-model="filters.year" placeholder="全部年份" clearable style="width: 130px" @change="load">
          <el-option v-for="y in years" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-select v-model="filters.tag" placeholder="全部标签" clearable style="width: 130px" @change="load">
          <el-option v-for="t in meta.tags" :key="t.id" :label="t.name" :value="t.name" />
        </el-select>
        <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 120px" @change="load">
          <el-option label="已发布" value="published" />
          <el-option label="草稿" value="draft" />
        </el-select>
        <el-input
          v-model="filters.q"
          placeholder="搜索标题 / 摘要 / 城市"
          style="width: 220px"
          clearable
          @change="load"
        />
        <span class="flex-1"></span>
        <el-button type="primary" :icon="Plus" @click="router.push('/admin/trips/new')">新建旅行</el-button>
      </div>

      <el-table v-loading="loading" :data="trips" stripe>
        <el-table-column label="封面" width="90">
          <template #default="{ row }">
            <el-image
              v-if="row.cover_photo"
              :src="photoUrl(row.cover_photo, 'thumb')"
              fit="cover"
              style="width: 64px; height: 48px; border-radius: 8px"
              :preview-src-list="[photoUrl(row.cover_photo, 'full')]"
              preview-teleported
            />
            <span v-else class="text-gray-300">—</span>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <router-link class="font-semibold" style="color: var(--ink)" :to="`/admin/trips/${row.id}`">{{ row.title }}</router-link>
            <div class="text-xs text-gray-400 mt-0.5">/trip/{{ row.slug }}</div>
          </template>
        </el-table-column>
        <el-table-column label="日期" width="190">
          <template #default="{ row }">
            <div class="text-sm">{{ dateRange(row.start_date, row.end_date) }}</div>
            <div class="text-xs text-gray-400">{{ row.days_count }} 天</div>
          </template>
        </el-table-column>
        <el-table-column label="路线" min-width="160">
          <template #default="{ row }">
            <span class="text-sm">{{ (row.country ? row.country + ' · ' : '') + row.route.join(' → ') }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" width="160">
          <template #default="{ row }">
            <el-tag v-for="t in row.tags" :key="t.id" size="small" class="mr-1">{{ t.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="router.push(`/admin/trips/${row.id}`)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
