import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api/client'

interface User {
  id: number
  strava_id: number
  firstname: string | null
  lastname: string | null
  profile_pic_url: string | null
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
