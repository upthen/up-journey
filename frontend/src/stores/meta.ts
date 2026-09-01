import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api'
import type { Member, Tag } from '@/types'

/** 跨页共享：家庭成员 + 标签字典（管理端编辑后 refresh()）。 */
export const useMetaStore = defineStore('meta', () => {
  const members = ref<Member[]>([])
  const tags = ref<Tag[]>([])
  const loaded = ref(false)

  async function refresh() {
    const data = await api.meta()
    members.value = data.members
    tags.value = data.tags
    loaded.value = true
  }

  async function ensure() {
    if (!loaded.value) await refresh()
  }

  return { members, tags, loaded, refresh, ensure }
})
