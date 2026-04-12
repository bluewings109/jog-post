import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api/client'

interface DataSource {
  provider: string
  external_id: string
}

interface User {
  id: number
  google_id: string
  email: string
  name: string | null
  picture: string | null
  data_sources: DataSource[]
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => user.value !== null)

  async function fetchMe() {
    try {
      const { data } = await apiClient.get<User>('/auth/me')
      user.value = data
    } catch {
      user.value = null
    }
  }

  async function logout() {
    await apiClient.post('/auth/logout')
    user.value = null
  }

  return { user, isLoggedIn, fetchMe, logout }
})
