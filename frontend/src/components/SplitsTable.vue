<template>
  <div class="splits-table-wrapper">
    <v-table density="compact" class="splits-table">
      <thead>
        <tr>
          <th class="text-left col-split">구간</th>
          <th class="text-right col-dist">거리</th>
          <th class="text-right col-time">시간</th>
          <th class="text-right col-pace">페이스</th>
          <th v-if="hasHR" class="text-right col-hr">평균심박</th>
          <th v-if="hasElev" class="text-right col-elev">고도차</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="split in splits"
          :key="split.split"
          :class="{ 'best-pace': split.split === bestSplit }"
        >
          <td class="col-split">
            <span class="split-label">{{ split.split }} km</span>
            <span v-if="split.split === bestSplit" class="best-badge">최고</span>
          </td>
          <td class="text-right col-dist">{{ formatDistance(split.distance) }}</td>
          <td class="text-right col-time font-mono">{{ formatTime(split.moving_time) }}</td>
          <td class="text-right col-pace font-weight-semibold font-mono">
            {{ split.average_speed ? formatPace(1000 / split.average_speed) : '-' }}
          </td>
          <td v-if="hasHR" class="text-right col-hr">
            <span :class="hrColor(split.average_heartrate)">
              {{ split.average_heartrate ? `${Math.round(split.average_heartrate)}` : '-' }}
            </span>
            <span class="unit">bpm</span>
          </td>
          <td v-if="hasElev" class="text-right col-elev">
            <template v-if="split.elevation_difference != null">
              <span :class="split.elevation_difference >= 0 ? 'elev-up' : 'elev-down'">
                {{ split.elevation_difference >= 0 ? '+' : '' }}{{ Math.round(split.elevation_difference) }}
              </span>
              <span class="unit">m</span>
            </template>
            <template v-else>-</template>
          </td>
        </tr>
      </tbody>
    </v-table>

    <div class="splits-footer text-caption text-medium-emphasis px-3 py-2">
      * 최고 페이스 구간 강조 표시 · 1km 단위 자동 분할 기준
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SplitMetric } from '@/api/activities'
import { formatDistance, formatPace, formatTime, hrColor } from '@/lib/format'

const props = defineProps<{ splits: SplitMetric[] }>()

const hasHR = computed(() => props.splits.some((s) => s.average_heartrate != null))
const hasElev = computed(() => props.splits.some((s) => s.elevation_difference != null))

const bestSplit = computed(() => {
  const withSpeed = props.splits.filter((s) => s.average_speed != null && s.average_speed > 0)
  if (!withSpeed.length) return null
  return withSpeed.reduce((best, s) =>
    (s.average_speed ?? 0) > (best.average_speed ?? 0) ? s : best,
  ).split
})
</script>

<style scoped>
.splits-table-wrapper {
  overflow-x: auto;
}

.splits-table :deep(th) {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.6;
  white-space: nowrap;
}

.splits-table :deep(td),
.splits-table :deep(th) {
  padding: 7px 10px !important;
}

.splits-table :deep(tbody tr:hover) {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.splits-table :deep(tbody tr.best-pace) {
  background: rgba(var(--v-theme-primary), 0.06);
}

.split-label {
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

.elev-up { color: #ef9a9a; }
.elev-down { color: #80cbc4; }

/* 심박 존 색상 */
:global(.hr-z1) { color: #64b5f6; }
:global(.hr-z2) { color: #81c784; }
:global(.hr-z3) { color: #ffb74d; }
:global(.hr-z4) { color: #ff8a65; }
:global(.hr-z5) { color: #e57373; }

.col-split { min-width: 72px; }
.col-dist  { min-width: 70px; }
.col-time  { min-width: 64px; }
.col-pace  { min-width: 80px; }
.col-hr    { min-width: 72px; }
.col-elev  { min-width: 60px; }

.splits-footer {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
</style>
