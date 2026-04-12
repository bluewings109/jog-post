<template>
  <v-row dense>
    <v-col v-for="stat in stats" :key="stat.label" cols="6" sm="4" md="3">
      <v-card rounded="lg" variant="tonal" color="primary" class="pa-3 text-center">
        <div class="text-caption text-medium-emphasis mb-1">{{ stat.label }}</div>
        <div class="text-h6 font-weight-bold">{{ stat.value }}</div>
        </v-card>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ActivityDetail } from '@/api/activities'
import { formatDistance, formatElevation, formatHR, formatPace, formatTime } from '@/lib/format'

const props = defineProps<{ activity: ActivityDetail }>()

const stats = computed(() => {
  const a = props.activity
  const items: Array<{ label: string; value: string }> = [
    { label: '거리', value: formatDistance(a.distance) },
    { label: '페이스', value: formatPace(a.average_pace_sec_per_km) },
    { label: '운동 시간', value: formatTime(a.moving_time) },
    { label: '총 시간', value: formatTime(a.elapsed_time) },
  ]
  if (a.average_heartrate != null)
    items.push({ label: '평균 심박', value: formatHR(a.average_heartrate) })
  if (a.max_heartrate != null)
    items.push({ label: '최대 심박', value: formatHR(a.max_heartrate) })
  if (a.total_elevation_gain != null)
    items.push({ label: '고도 획득', value: formatElevation(a.total_elevation_gain) })
  if (a.calories != null)
    items.push({ label: '칼로리', value: `${Math.round(a.calories)} kcal` })
  if (a.average_cadence != null)
    items.push({ label: '케이던스', value: `${Math.round(a.average_cadence)} spm` })
  if (a.suffer_score != null)
    items.push({ label: '고통 점수', value: String(a.suffer_score) })
  return items
})
</script>
