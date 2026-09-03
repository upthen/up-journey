<script setup lang="ts">
/** 旅行管理列表：按年份/标签/状态/关键词筛选（user story 13），编辑/删除（story 12）。 */
import { Delete, Edit, Plus, Search } from '@element-plus/icons-vue'
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
const draftCount = computed(() => trips.value.filter((t) => t.status === 'draft').length)

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
    <section class="ad-panel trip-list">
      <!-- 面板头：左标题+统计，右主操作 -->
      <div class="list-head">
        <div class="list-title">
          <h4>旅行管理</h4>
          <span class="count">共 {{ trips.length }} 篇<template v-if="draftCount"> · {{ draftCount }} 篇草稿</template></span>
        </div>
        <el-button type="primary" :icon="Plus" @click="router.push('/admin/trips/new')">新建旅行</el-button>
      </div>
      <p class="hint">草稿不会出现在展示端；发布后地图、编年、名录即时更新。</p>

      <!-- 筛选条：浅底容器与表格分层；窄屏 wrap 也不错乱 -->
      <div class="list-filters">
        <el-select v-model="filters.year" placeholder="全部年份" clearable class="f-select" @change="load">
          <el-option v-for="y in years" :key="y" :label="y + ' 年'" :value="y" />
        </el-select>
        <el-select v-model="filters.tag" placeholder="全部标签" clearable class="f-select" @change="load">
          <el-option v-for="t in meta.tags" :key="t.id" :label="t.name" :value="t.name" />
        </el-select>
        <el-select v-model="filters.status" placeholder="全部状态" clearable class="f-select" @change="load">
          <el-option label="已发布" value="published" />
          <el-option label="草稿" value="draft" />
        </el-select>
        <span class="spacer"></span>
        <el-input
          v-model="filters.q"
          placeholder="搜索标题 / 摘要 / 城市"
          class="f-search"
          clearable
          :prefix-icon="Search"
          @change="load"
          @clear="load"
        />
      </div>

      <el-table v-loading="loading" :data="trips">
        <el-table-column label="封面" width="88" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.cover_photo"
              :src="photoUrl(row.cover_photo, 'thumb')"
              fit="cover"
              class="cover"
              :preview-src-list="[photoUrl(row.cover_photo, 'full')]"
              preview-teleported
            />
            <span v-else class="cover cover-empty">无封面</span>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220">
          <template #default="{ row }">
            <router-link class="t-title" :to="`/admin/trips/${row.id}`">{{ row.title }}</router-link>
            <div class="t-slug">/trip/{{ row.slug }}</div>
          </template>
        </el-table-column>
        <el-table-column label="日期" width="160">
          <template #default="{ row }">
            <div class="t-date">{{ dateRange(row.start_date, row.end_date) }}</div>
            <div class="t-days">{{ row.days_count }} 天</div>
          </template>
        </el-table-column>
        <el-table-column label="路线" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="t-route">{{ (row.country ? row.country + ' · ' : '') + row.route.join(' → ') }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="130">
          <template #default="{ row }">
            <div v-if="row.tags.length" class="t-tags">
              <el-tag v-for="t in row.tags" :key="t.id" size="small" effect="plain">{{ t.name }}</el-tag>
            </div>
            <span v-else class="t-days">—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="84" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small" effect="light" round>
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="router.push(`/admin/trips/${row.id}`)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="filters.q || filters.year || filters.tag || filters.status ? '没有匹配的旅行，试试放宽筛选条件' : '还没有旅行记录，点右上角「新建旅行」开始'" :image-size="72" />
        </template>
      </el-table>
    </section>
  </div>
</template>
