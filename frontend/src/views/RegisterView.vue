<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center">
    <div class="w-full max-w-md px-8 py-10 bg-gray-900 rounded-2xl border border-gray-800">

      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white tracking-tight">Papyrus</h1>
        <p class="text-gray-400 mt-2 text-sm">创建你的账号</p>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="mb-4 px-4 py-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
        {{ error }}
      </div>

      <!-- 表单 -->
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">显示名称（可选）</label>
          <input
            v-model="displayName"
            type="text"
            placeholder="你的名字"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">邮箱</label>
          <input
            v-model="email"
            type="email"
            placeholder="your@email.com"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <!-- 登录链接 -->
      <p class="text-center text-gray-500 text-sm mt-6">
        已有账号？
        <RouterLink to="/login" class="text-blue-400 hover:text-blue-300 transition-colors">
          立即登录
        </RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const displayName = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (!email.value || !password.value) {
    error.value = '请填写邮箱和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await api.register(email.value, password.value, displayName.value || undefined)
    authStore.setToken(data.access_token, displayName.value || email.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>