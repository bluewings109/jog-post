<template>
  <div class="lap-table-wrapper">
    <v-table density="compact" class="lap-table">
      <thead>
        <tr>
          <th class="text-left col-lap">랩</th>
          <th class="text-right col-dist">거리</th>
          <th class="text-right col-time">시간</th>
          <th class="text-right col-pace">페이스</th>
          <th v-if="hasHR" class="text-right col-hr">평균심박</th>
          <th v-if="hasMaxHR" class="text-right col-hr">최대심박</th>
          <th v-if="hasCadence" class="text-right col-cad">케이던스</th>
          <th v-if="hasElevation" class="text-right col-elev">고도</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="lap in laps"
          :key="lap.id"
          :class="{ 'best-pace': lap.id === bestPaceLapId }"
        >
          <td class="col-lap">
            <span class="lap-index">{{ lap.lap_index }}</span>
            <span v-if="lap.id === bestPaceLapId" class="best-badge">최고</span>
          </td>
          <td class="text-right col-dist">{{ formatDistance(lap.distance) }}</td>
          <td class="text-right col-time font-mono">{{ formatTime(lap.moving_time) }}</td>
          <td class="text-right col-pace font-weight-semibold font-mono">
            {{ lap.average_speed ? formatPace(1000 / lap.average_speed) : '-' }}
          </td>
          <td v-if="hasHR" class="text-right col-hr">
            <span :class="hrColor(lap.average_heartrate)">
              {{ lap.average_heartrate ? `${Math.round(lap.average_heartrate)}` : '-' }}
            </span>
            <span class="unit">bpm</span>
          </td>
          <td v-if="hasMaxHR" class="text-right col-hr">
            <span>{{ lap.max_heartrate ? `${Math.round(lap.max_heartrate)}` : '-' }}</span>
            <span class="unit">bpm</span>
          </td>
          <td v-if="hasCadence" class="text-right col-cad">
            {{ lap.average_cadence ? `${Math.round(lap.average_cadence)}` : '-' }}
            <span class="unit">spm</span>
          </td>
          <td v-if="hasElevation" class="text-right col-elev">
            {{ lap.total_elevation_gain != null ? `+${Math.round(lap.total_elevation_gain)}` : '-' }}
            <span class="unit">m</span>
          </td>
        </tr>
      </tbody>
    </v-table>

    <div class="lap-footer text-caption text-medium-emphasis px-3 py-2">
      * 최고 페이스 랩 강조 표시 · Strava는 랩별 최소 심박을 제공하지 않습니다
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Lap } from '@/api/activities'
import { formatDistance, formatPace, formatTime, hrColor } from '@/lib/format'

const props = defineProps<{ laps: Lap[] }>()

const hasHR = computed(() => props.laps.some((l) => l.average_heartrate != null))
const hasMaxHR = computed(() => props.laps.some((l) => l.max_heartrate != null))
const hasCadence = computed(() => props.laps.some((l) => l.average_cadence != null))
const hasElevation = computed(() => props.laps.some((l) => l.total_elevation_gain != null))

/** 페이스가 가장 빠른(낮은) 랩 ID */
const bestPaceLapId = computed(() => {
  const withSpeed = props.laps.filter((l) => l.average_speed != null && l.average_speed > 0)
  if (!withSpeed.length) return null
  return withSpeed.reduce((best, l) =>
    (l.average_speed ?? 0) > (best.average_speed ?? 0) ? l : best,
  ).id
})

</script>

<style scoped>
.lap-table-wrapper {
  overflow-x: auto;
}

.lap-table :deep(th) {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.6;
  white-space: nowrap;
}

.lap-table :deep(td),
.lap-table :deep(th) {
  padding: 7px 10px !important;
}

.lap-table :deep(tbody tr:hover) {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.lap-table :deep(tbody tr.best-pace) {
  background: rgba(var(--v-theme-primary), 0.06);
}

.lap-index {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.best-badge {
  display: inline-block;
  margin-left: 6px;
  font-size: 0.6rem;
  background: rgb(var(--v-theme-primary));
  color: white;
  border-radius: 4px;
  padding: 1px 4px;
  vertical-align: middle;
  line-height: 1.4;
}

.font-mono {
  font-variant-numeric: tabular-nums;
}

.unit {
  font-size: 0.68rem;
  opacity: 0.55;
  margin-left: 1px;
}

/* 심박 존 색상 */
.hr-z1 { color: #64b5f6; }
.hr-z2 { color: #81c784; }
.hr-z3 { color: #ffb74d; }
.hr-z4 { color: #ff8a65; }
.hr-z5 { color: #e57373; }

.col-lap  { min-width: 56px; }
.col-dist { min-width: 70px; }
.col-time { min-width: 64px; }
.col-pace { min-width: 80px; }
.col-hr   { min-width: 72px; }
.col-cad  { min-width: 72px; }
.col-elev { min-width: 60px; }

.lap-footer {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
</style>
