<template>
  <v-card
    class="activity-card"
    :to="`/activities/${activity.id}`"
    rounded="lg"
    elevation="2"
    hover
  >
    <v-card-text class="pa-4">
      <div class="d-flex align-center justify-space-between mb-2">
        <span class="text-caption text-medium-emphasis">{{ formatDate(activity.start_date_local) }}</span>
        <v-chip size="x-small" color="primary" variant="tonal">
          {{ activity.sport_type ?? 'Run' }}
        </v-chip>
      </div>

      <div class="text-subtitle-1 font-weight-bold mb-3 text-truncate">
        {{ activity.name ?? '이름 없음' }}
      </div>

      <v-row dense>
        <v-col cols="4">
          <div class="stat-label">거리</div>
          <div class="stat-value">{{ formatDistance(activity.distance) }}</div>
        </v-col>
        <v-col cols="4">
          <div class="stat-label">페이스</div>
          <div class="stat-value">{{ formatPace(activity.average_pace_sec_per_km) }}</div>
        </v-col>
        <v-col cols="4">
          <div class="stat-label">시간</div>
          <div class="stat-value">{{ formatTime(activity.moving_time) }}</div>
        </v-col>
      </v-row>

      <v-row v-if="activity.average_heartrate || activity.total_elevation_gain" dense class="mt-1">
        <v-col v-if="activity.average_heartrate" cols="4">
          <div class="stat-label">심박</div>
          <div class="stat-value">{{ formatHR(activity.average_heartrate) }}</div>
        </v-col>
        <v-col v-if="activity.total_elevation_gain" cols="4">
          <div class="stat-label">고도</div>
          <div class="stat-value">{{ formatElevation(activity.total_elevation_gain) }}</div>
        </v-col>
        <v-col v-if="activity.pr_count > 0" cols="4">
          <div class="stat-label">PR</div>
          <div class="stat-value">🏆 {{ activity.pr_count }}</div>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import type { Activity } from '@/api/activities'
import { formatDate, formatDistance, formatElevation, formatHR, formatPace, formatTime } from '@/lib/format'

defineProps<{ activity: Activity }>()
</script>

<style scoped>
.activity-card {
  transition: transform 0.15s ease;
}

.activity-card:hover {
  transform: translateY(-2px);
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 0.95rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
</style>
