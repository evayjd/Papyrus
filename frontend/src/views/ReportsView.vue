<template>
  <div class="min-h-screen bg-gray-950">

    <!-- 顶部导航 -->
    <nav class="bg-gray-900 border-b border-gray-800 px-8 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <RouterLink to="/" class="text-gray-400 hover:text-white transition-colors text-sm">
          ← 返回
        </RouterLink>
        <h1 class="text-white font-semibold">历史报告</h1>
      </div>
      <span class="text-sm text-gray-400">{{ authStore.displayName }}</span>
    </nav>

    <div class="max-w-4xl mx-auto px-8 py-8">

      <!-- 加载中 -->
      <div v-if="loading" class="text-center text-gray-400 py-20">
        加载中...
      </div>

      <!-- 空状态 -->
      <div v-else-if="reports.length === 0" class="text-center py-20">
        <p class="text-4xl mb-4">📭</p>
        <p class="text-gray-400">还没有报告，去研究一些课题吧</p>
        <RouterLink to="/" class="mt-4 inline-block text-blue-400 hover:text-blue-300 text-sm transition-colors">
          开始研究 →
        </RouterLink>
      </div>

      <!-- 报告列表 -->
      <div v-else class="space-y-3">
        <div
          v-for="report in reports"
          :key="report.id"
          class="bg-gray-900 border border-gray-800 rounded-xl px-6 py-4 flex items-center justify-between hover:border-gray-700 transition-colors cursor-pointer"
          @click="goToReport(report.id)"
        >
          <div>
            <h3 class="text-white font-medium">{{ report.title || '未命名报告' }}</h3>
            <p class="text-gray-500 text-sm mt-0.5">{{ formatDate(report.created_at) }}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-500">查看 →</span>
            <button
              @click.stop="deleteReport(report.id)"
              class="text-xs text-red-500 hover:text-red-400 transition-colors"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const reports = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  await loadReports()
})

async function loadReports() {
  try {
    reports.value = await api.listReports()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goToReport(id: string) {
  router.push(`/reports/${id}`)
}

async function deleteReport(id: string) {
  if (!confirm('确定删除这份报告吗？')) return
  try {
    await api.deleteReport(id)
    reports.value = reports.value.filter(r => r.id !== id)
  } catch (e) {
    console.error(e)
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>