<template>
  <div class="min-h-screen bg-gray-950">

    <!-- 顶部导航 -->
    <nav class="bg-gray-900 border-b border-gray-800 px-8 py-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <RouterLink to="/reports" class="text-gray-400 hover:text-white transition-colors text-sm">
          ← 返回报告列表
        </RouterLink>
        <h1 class="text-white font-semibold">{{ report?.title || '报告详情' }}</h1>
      </div>
      <span class="text-sm text-gray-400">{{ formatDate(report?.created_at) }}</span>
    </nav>

    <div class="max-w-4xl mx-auto px-8 py-8">

      <!-- 加载中 -->
      <div v-if="loading" class="text-center text-gray-400 py-20">
        加载中...
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="text-center text-red-400 py-20">
        {{ error }}
      </div>

      <!-- 报告内容 -->
      <div v-else-if="report">

        <!-- 评估分数 -->
        <div v-if="evaluation" class="bg-gray-900 border border-gray-800 rounded-xl px-6 py-4 mb-6">
          <h3 class="text-white font-medium mb-3">报告质量评估</h3>
          <div class="grid grid-cols-3 gap-4">
            <div class="text-center">
              <p class="text-2xl font-bold" :class="scoreColor(evaluation.faithfulness)">
                {{ (evaluation.faithfulness * 100).toFixed(0) }}%
              </p>
              <p class="text-xs text-gray-500 mt-1">忠实度</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold" :class="scoreColor(evaluation.answer_relevancy)">
                {{ (evaluation.answer_relevancy * 100).toFixed(0) }}%
              </p>
              <p class="text-xs text-gray-500 mt-1">答案相关性</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold" :class="scoreColor(evaluation.context_recall)">
                {{ (evaluation.context_recall * 100).toFixed(0) }}%
              </p>
              <p class="text-xs text-gray-500 mt-1">召回率</p>
            </div>
          </div>
        </div>

        <!-- Markdown 报告 -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-8">
          <div
            class="prose prose-invert prose-sm max-w-none"
            v-html="marked(report.content?.markdown || '')"
          ></div>
        </div>

        <!-- 引用论文 -->
        <div v-if="report.content?.papers?.length" class="mt-6 bg-gray-900 border border-gray-800 rounded-xl px-6 py-4">
          <h3 class="text-white font-medium mb-3">引用论文</h3>
          <div class="space-y-2">
            <div
              v-for="paper in report.content.papers"
              :key="paper.arxiv_id"
              class="text-sm text-gray-400"
            >
              <span class="text-white">{{ paper.title }}</span>
              <span class="text-gray-600 mx-2">·</span>
              <span>{{ paper.authors?.join(', ') }}</span>
              <span class="text-gray-600 mx-2">·</span>
              <span>{{ paper.published }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api'
import { marked } from 'marked'

const route = useRoute()
const authStore = useAuthStore()

const report = ref<any>(null)
const evaluation = ref<any>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  await loadReport()
})

async function loadReport() {
  try {
    const id = route.params.id as string
    report.value = await api.getReport(id)

    // 加载评估结果
    try {
      evaluation.value = await api.getEvaluation(id)
    } catch (e) {
      // 没有评估结果不报错
    }
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function scoreColor(score: number) {
  if (score >= 0.7) return 'text-green-400'
  if (score >= 0.4) return 'text-yellow-400'
  return 'text-red-400'
}

function formatDate(dateStr?: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>