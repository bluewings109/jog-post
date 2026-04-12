import { ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchActivities, fetchActivity } from '@/api/activities'
import type { Activity, ActivityDetail } from '@/api/activities'

export const useActivitiesStore = defineStore('activities', () => {
  const activities = ref<Activity[]>([])
  const currentActivity = ref<ActivityDetail | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function loadActivities(page = 1, perPage = 20) {
    loading.value = true
    try {
      const { data } = await fetchActivities(page, perPage)
      activities.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function loadActivity(id: number) {
    loading.value = true
    try {
      const { data } = await fetchActivity(id)
      currentActivity.value = data
    } finally {
      loading.value = false
    }
  }

  return { activities, currentActivity, total, loading, loadActivities, loadActivity }
})
