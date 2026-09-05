<script setup lang="ts">
/** 管理端登录：唯一入口是管理员密码（展示端永远免密）。 */
import { Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api'

const router = useRouter()
const route = useRoute()
const password = ref('')
const loading = ref(false)
const unconfigured = ref(false)
// 401 拦截器整页跳转会带 expired=1：告知「会话过期」而非「密码错误」，
// 并安抚用户——未保存内容已自动存在本地，登录回到编辑页后可恢复（#12）
const expired = route.query.expired === '1'

async function submit() {
  if (!password.value) return
  loading.value = true
  try {
    await api.admin.login(password.value)
    const next = typeof route.query.next === 'string' && route.query.next.startsWith('/admin') ? route.query.next : '/admin/trips'
    router.push(next)
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status
    if (status === 503) {
      unconfigured.value = true
    } else {
      ElMessage.error('密码不正确')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="login-card" @submit.prevent="submit">
      <div class="mark">🧭</div>
      <h1>游迹 · 管理端</h1>
      <p class="sub">家庭记录者的入口——展示端无需登录，这里需要管理员密码。</p>
      <el-input
        v-model="password"
        type="password"
        size="large"
        placeholder="管理员密码"
        :prefix-icon="Lock"
        show-password
        autofocus
        @keydown.enter="submit"
      />
      <el-button type="primary" size="large" native-type="submit" :loading="loading" style="width: 100%; margin-top: 14px">
        登 录
      </el-button>
      <p v-if="expired" class="warn">
        登录已过期，请重新登录。编辑页未保存的内容已自动保存在本机浏览器中，登录回到编辑页后可恢复。
      </p>
      <p v-if="unconfigured" class="warn">
        服务端尚未配置管理密码：在 NAS 部署目录的 .env 里设置 <code>ADMIN_PASSWORD</code> 并重启 api 容器。
      </p>
      <router-link class="back" to="/">← 回展示端</router-link>
    </form>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f1ec;
  padding: 20px;
}
.login-card {
  width: 380px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(31, 42, 51, 0.06), 0 12px 32px rgba(31, 42, 51, 0.1);
  padding: 36px 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.login-card .mark {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: var(--coral);
  color: #fff;
  font-size: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
}
.login-card h1 {
  font-size: 20px;
  text-align: center;
}
.login-card .sub {
  font-size: 12.5px;
  color: var(--gray);
  text-align: center;
  margin-bottom: 18px;
}
.login-card .warn {
  margin-top: 14px;
  font-size: 12.5px;
  color: #c0392b;
  background: #fdeeee;
  border-radius: 10px;
  padding: 10px 12px;
}
.login-card .warn code {
  font-size: 11.5px;
}
.login-card .back {
  margin-top: 18px;
  text-align: center;
  font-size: 12.5px;
  color: var(--ink-2);
}
</style>
