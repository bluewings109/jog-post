import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  fetchWeeklyStats,
  fetchMonthlyStats,
  fetchYearlyStats,
  type PeriodStatsItem,
} from '@/api/statistics'

export type StatMode = 'week' | 'month' | 'year'

export const useStatisticsStore = defineStore('statistics', () => {
  const mode = ref<StatMode>('month')
  const data = ref<PeriodStatsItem[]>([])
  const loading = ref(false)

  const now = new Date()
  const selectedYear = ref(now.getFullYear())
  const selectedMonth = ref(now.getMonth() + 1)

  const periodLabel = computed(() => {
    if (mode.value === 'week') return `${selectedYear.value}년 ${selectedMonth.value}월`
    if (mode.value === 'month') return `${selectedYear.value}년`
    return '전체 기간'
  })

  const isCurrentPeriod = computed(() => {
    const n = new Date()
    if (mode.value === 'week')
      return selectedYear.value === n.getFullYear() && selectedMonth.value === n.getMonth() + 1
    if (mode.value === 'month') return selectedYear.value === n.getFullYear()
    return true
  })

  async function loadStats() {
    loading.value = true
    try {
      if (mode.value === 'week') {
        const { data: res } = await fetchWeeklyStats(selectedYear.value, selectedMonth.value)
        data.value = res.weeks
      } else if (mode.value === 'month') {
        const { data: res } = await fetchMonthlyStats(selectedYear.value)
        data.value = res.months
      } else {
        const { data: res } = await fetchYearlyStats()
        data.value = res.years
      }
    } finally {
      loading.value = false
    }
  }

  function setMode(m: StatMode) {
    mode.value = m
    const n = new Date()
    selectedYear.value = n.getFullYear()
    selectedMonth.value = n.getMonth() + 1
    loadStats()
  }

  function prevPeriod() {
    if (mode.value === 'week') {
      if (selectedMonth.value === 1) {
        selectedYear.value--
        selectedMonth.value = 12
      } else {
        selectedMonth.value--
      }
    } else if (mode.value === 'month') {
      selectedYear.value--
    }
    loadStats()
  }

  function nextPeriod() {
    if (mode.value === 'week') {
      if (selectedMonth.value === 12) {
        selectedYear.value++
        selectedMonth.value = 1
      } else {
        selectedMonth.value++
      }
    } else if (mode.value === 'month') {
      selectedYear.value++
    }
    loadStats()
  }

  return {
    mode,
    data,
    loading,
    selectedYear,
    selectedMonth,
    periodLabel,
    isCurrentPeriod,
    loadStats,
    setMode,
    prevPeriod,
    nextPeriod,
  }
})
