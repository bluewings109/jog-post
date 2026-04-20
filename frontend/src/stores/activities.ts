import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchActivities, fetchActivity } from '@/api/activities'
import type { Activity, ActivityDetail } from '@/api/activities'

type ViewMode = 'week' | 'month' | 'year'

function getPeriodRange(mode: ViewMode, offset: number) {
  const now = new Date()

  if (mode === 'month') {
    const d = new Date(now.getFullYear(), now.getMonth() + offset, 1)
    const start = new Date(d.getFullYear(), d.getMonth(), 1)
    const end = new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59)
    return {
      start: start.toISOString(),
      end: end.toISOString(),
      label: `${d.getFullYear()}년 ${d.getMonth() + 1}월`,
    }
  }

  if (mode === 'week') {
    const base = new Date(now)
    base.setDate(base.getDate() + offset * 7)
    const day = base.getDay() || 7
    const monday = new Date(base)
    monday.setDate(base.getDate() - day + 1)
    monday.setHours(0, 0, 0, 0)
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    sunday.setHours(23, 59, 59, 999)
    const jan4 = new Date(monday.getFullYear(), 0, 4)
    const weekNum = Math.ceil(
      ((monday.getTime() - jan4.getTime()) / 86400000 + jan4.getDay() + 1) / 7,
    )
    return {
      start: monday.toISOString(),
      end: sunday.toISOString(),
      label: `${monday.getFullYear()}년 ${weekNum}주차`,
    }
  }

  // year
  const year = now.getFullYear() + offset
  return {
    start: new Date(year, 0, 1).toISOString(),
    end: new Date(year, 11, 31, 23, 59, 59).toISOString(),
    label: `${year}년`,
  }
}

export const useActivitiesStore = defineStore('activities', () => {
  const activities = ref<Activity[]>([])
  const currentActivity = ref<ActivityDetail | null>(null)
  const total = ref(0)
  const loading = ref(false)

  const viewMode = ref<ViewMode>('month')
  const periodOffset = ref(0)

  const periodLabel = computed(() => getPeriodRange(viewMode.value, periodOffset.value).label)
  const isCurrentPeriod = computed(() => periodOffset.value === 0)

  async function loadActivities(page = 1, perPage = 20) {
    loading.value = true
    const { start, end } = getPeriodRange(viewMode.value, periodOffset.value)
    try {
      const { data } = await fetchActivities(page, perPage, start, end)
      activities.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
    periodOffset.value = 0
    loadActivities(1)
  }

  function prevPeriod() {
    periodOffset.value--
    loadActivities(1)
  }

  function nextPeriod() {
    periodOffset.value++
    loadActivities(1)
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

  return {
    activities,
    currentActivity,
    total,
    loading,
    viewMode,
    periodLabel,
    isCurrentPeriod,
    loadActivities,
    loadActivity,
    setViewMode,
    prevPeriod,
    nextPeriod,
  }
})
