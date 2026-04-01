import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const displayName = ref<string | null>(localStorage.getItem('displayName'))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken: string, name: string) {
    token.value = newToken
    displayName.value = name
    localStorage.setItem('token', newToken)
    localStorage.setItem('displayName', name)
  }

  function logout() {
    token.value = null
    displayName.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('displayName')
  }

  return { token, displayName, isLoggedIn, setToken, logout }
})