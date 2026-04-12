<template>
  <v-container>
    <h1 class="text-h5 mb-4">내 달리기 기록</h1>
    <v-progress-circular v-if="store.loading" indeterminate />
    <v-row v-else>
      <v-col v-for="activity in store.activities" :key="activity.id" cols="12" sm="6" md="4">
        <v-card :to="{ name: 'activity-detail', params: { id: activity.id } }" hover>
          <v-card-title>{{ activity.name ?? '달리기' }}</v-card-title>
          <v-card-subtitle>{{ formatDate(activity.start_date) }}</v-card-subtitle>
          <v-card-text>
            <div>{{ formatDistance(activity.distance) }}</div>
            <div>{{ formatPace(activity.average_speed) }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useActivitiesStore } from '@/stores/activities'

const store = useActivitiesStore()

onMounted(() => store.loadActivities())

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

function formatDistance(meters: number | null) {
  if (!meters) return '-'
  return `${(meters / 1000).toFixed(2)} km`
}

function formatPace(mps: number | null) {
  if (!mps) return '-'
  const secPerKm = 1000 / mps
  const min = Math.floor(secPerKm / 60)
  const sec = Math.round(secPerKm % 60)
  return `${min}'${String(sec).padStart(2, '0')}" /km`
}
</script>
