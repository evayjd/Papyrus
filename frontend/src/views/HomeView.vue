<template>
  <div class="min-h-screen bg-gray-950 flex">

    <!-- 侧边栏 -->
    <aside class="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div class="px-6 py-5 border-b border-gray-800">
        <h1 class="text-xl font-bold text-white">Papyrus</h1>
        <p class="text-xs text-gray-500 mt-0.5">AI 研究助手</p>
      </div>

      <div class="flex-1 px-3 py-4 overflow-hidden flex flex-col">
        <button
          @click="newResearch"
          class="w-full px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
        >
          <span>+</span> 新建研究
        </button>

        <div class="mt-4 flex-1 overflow-y-auto space-y-1">
          <p class="text-xs text-gray-500 px-2 mb-2">最近研究</p>
          <div
            v-for="session in sessions"
            :key="session.id"
            @click="selectSession(session.id)"
            class="px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors"
            :class="currentSessionId === session.id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'"
          >
            {{ session.title || '未命名研究' }}
          </div>
        </div>
      </div>

      <div class="px-4 py-4 border-t border-gray-800 flex items-center justify-between">
        <span class="text-sm text-gray-400">{{ authStore.displayName }}</span>
        <button @click="handleLogout" class="text-xs text-gray-500 hover:text-white transition-colors">
          退出
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">

      <!-- 空状态 -->
      <div v-if="!currentSessionId && !isNewResearch" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <p class="text-4xl mb-4">📜</p>
          <h2 class="text-xl font-semibold text-white mb-2">开始你的研究</h2>
          <p class="text-gray-400 text-sm">点击「新建研究」输入研究课题</p>
        </div>
      </div>

      <!-- 研究界面 -->
      <div v-else class="flex-1 flex flex-col overflow-hidden">

        <div class="flex-1 overflow-y-auto px-8 py-6 space-y-4" ref="messagesContainer">
          <div v-for="(msg, i) in messages" :key="i">
            <div v-if="msg.type === 'progress'" class="flex items-start gap-3">
              <div class="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span class="text-xs text-white">✦</span>
              </div>
              <div class="bg-gray-800 rounded-lg px-4 py-2.5 text-sm text-gray-300">
                <span class="text-xs text-gray-500 mr-2">[{{ msg.node }}]</span>
                {{ msg.message }}
              </div>
            </div>

            <div v-else-if="msg.type === 'report'" class="bg-gray-800 rounded-xl p-6">
              <h3 class="text-white font-semibold mb-4">研究报告</h3>
              <div class="prose prose-invert prose-sm max-w-none text-gray-300" v-html="marked(msg.report)"></div>
            </div>

            <div v-else-if="msg.type === 'error'" class="px-4 py-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
              {{ msg.message }}
            </div>
          </div>

          <div v-if="isRunning" class="flex items-center gap-3">
            <div class="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
              <span class="text-xs text-white">⟳</span>
            </div>
            <span class="text-gray-400 text-sm">正在研究中...</span>
          </div>
        </div>

        <div class="px-8 py-4 border-t border-gray-800">
          <div class="flex gap-3">
            <input
              v-model="query"
              @keydown.enter="startResearch"
              :disabled="isRunning"
              placeholder="输入研究课题，例如：RAG 最新进展..."
              class="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
            />
            <button
              @click="startResearch"
              :disabled="isRunning || !query"
              class="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors"
            >
              {{ isRunning ? '研究中' : '开始' }}
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api, createWebSocket } from '@/api'
import { marked } from 'marked'

const router = useRouter()
const authStore = useAuthStore()

const sessions = ref<any[]>([])
const currentSessionId = ref<string | null>(null)
const messages = ref<any[]>([])
const query = ref('')
const isRunning = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const isNewResearch = ref(false)

onMounted(async () => {
  await loadSessions()
})

async function loadSessions() {
  try {
    sessions.value = await api.listSessions()
  } catch (e) {
    console.error(e)
  }
}

function newResearch() {
  currentSessionId.value = null
  messages.value = []
  query.value = ''
  isNewResearch.value = true
}

async function selectSession(id: string) {
  currentSessionId.value = id
  isNewResearch.value = false
  messages.value = []

  try {
    const reports = await api.listReports()
    const report = reports.find((r: any) => r.session_id === id)
    if (report) {
      const detail = await api.getReport(report.id)
      messages.value.push({
        type: 'report',
        report: detail.content?.markdown || '报告内容为空',
      })
    }
  } catch (e) {
    console.error(e)
  }
}

async function startResearch() {
  if (!query.value || isRunning.value) return

  isRunning.value = true
  messages.value = []
  isNewResearch.value = false

  try {
    const session = await api.createSession(query.value)
    currentSessionId.value = session.id
    await loadSessions()

    const ws = createWebSocket(session.id)

    ws.onopen = () => {
      ws.send(JSON.stringify({ token: authStore.token }))
      ws.send(JSON.stringify({ query: query.value }))
      query.value = ''
    }

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      messages.value.push(data)
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
      if (data.type === 'done' || data.type === 'error') {
        isRunning.value = false
        await loadSessions()
      }
    }

    ws.onerror = () => {
      messages.value.push({ type: 'error', message: 'WebSocket 连接错误' })
      isRunning.value = false
    }

  } catch (e: any) {
    messages.value.push({ type: 'error', message: e.message })
    isRunning.value = false
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>