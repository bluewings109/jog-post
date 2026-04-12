<template>
  <v-table density="compact" class="lap-table">
    <thead>
      <tr>
        <th class="text-left">#</th>
        <th class="text-right">거리</th>
        <th class="text-right">페이스</th>
        <th class="text-right">시간</th>
        <th v-if="hasHR" class="text-right">심박</th>
        <th v-if="hasCadence" class="text-right">케이던스</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="lap in laps" :key="lap.id">
        <td class="text-medium-emphasis">{{ lap.lap_index }}</td>
        <td class="text-right">{{ formatDistance(lap.distance) }}</td>
        <td class="text-right font-weight-medium">
          {{ formatPace(lap.average_speed ? 1000 / lap.average_speed : null) }}
        </td>
        <td class="text-right">{{ formatTime(lap.moving_time) }}</td>
        <td v-if="hasHR" class="text-right">{{ formatHR(lap.average_heartrate) }}</td>
        <td v-if="hasCadence" class="text-right">
          {{ lap.average_cadence ? `${Math.round(lap.average_cadence)} spm` : '-' }}
        </td>
      </tr>
    </tbody>
  </v-table>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Lap } from '@/api/activities'
import { formatDistance, formatHR, formatPace, formatTime } from '@/lib/format'

const props = defineProps<{ laps: Lap[] }>()

const hasHR = computed(() => props.laps.some((l) => l.average_heartrate != null))
const hasCadence = computed(() => props.laps.some((l) => l.average_cadence != null))
</script>

<style scoped>
.lap-table :deep(th) {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.7;
}

.lap-table :deep(td),
.lap-table :deep(th) {
  padding: 6px 8px !important;
}
</style>
