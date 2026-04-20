<template>
  <v-container max-width="860">
    <div class="d-flex align-center justify-space-between mb-4">
      <h1 class="text-h5 font-weight-bold">통계</h1>
    </div>

    <!-- 모드 선택 + 기간 네비게이션 -->
    <v-row align="center" justify="center" class="mb-4" no-gutters>
      <v-btn-toggle
        :model-value="store.mode"
        mandatory
        density="compact"
        color="deep-orange"
        class="mr-4"
        @update:model-value="store.setMode($event)"
      >
        <v-btn value="week" size="small">주별</v-btn>
        <v-btn value="month" size="small">월별</v-btn>
        <v-btn value="year" size="small">연별</v-btn>
      </v-btn-toggle>

      <template v-if="store.mode !== 'year'">
        <v-btn icon="mdi-chevron-left" variant="text" density="compact" @click="store.prevPeriod()" />
        <span
          class="text-body-1 font-weight-medium mx-2"
          style="min-width: 130px; text-align: center"
        >
          {{ store.periodLabel }}
        </span>
        <v-btn
          icon="mdi-chevron-right"
          variant="text"
          density="compact"
          :disabled="store.isCurrentPeriod"
          @click="store.nextPeriod()"
        />
      </template>
      <template v-else>
        <span class="text-body-1 font-weight-medium mx-2">{{ store.periodLabel }}</span>
      </template>
    </v-row>

    <v-progress-linear v-if="store.loading" indeterminate color="deep-orange" class="mb-4" />

    <template v-if="!store.loading">
      <!-- 빈 상태 -->
      <div
        v-if="store.data.length === 0"
        class="text-center py-12 text-medium-emphasis"
      >
        <v-icon size="64" class="mb-3">mdi-chart-bar</v-icon>
        <div class="text-h6">{{ store.periodLabel }}에 활동 데이터가 없어요</div>
        <div class="text-body-2 mt-1">Strava 동기화 후 활동이 있는 기간을 선택해보세요.</div>
      </div>

      <template v-else>
        <!-- 요약 카드 -->
        <v-row class="mb-4" dense>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="deep-orange">
              <v-card-text class="text-center pa-3">
                <div class="text-caption text-medium-emphasis">총 거리</div>
                <div class="text-h6 font-weight-bold">{{ totalDistance }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="deep-orange">
              <v-card-text class="text-center pa-3">
                <div class="text-caption text-medium-emphasis">총 활동</div>
                <div class="text-h6 font-weight-bold">{{ totalActivities }}회</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="deep-orange">
              <v-card-text class="text-center pa-3">
                <div class="text-caption text-medium-emphasis">총 시간</div>
                <div class="text-h6 font-weight-bold">{{ totalTime }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="tonal" color="deep-orange">
              <v-card-text class="text-center pa-3">
                <div class="text-caption text-medium-emphasis">평균 페이스</div>
                <div class="text-h6 font-weight-bold">{{ avgPace }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- SVG 바 차트 -->
        <v-card class="mb-4" variant="outlined">
          <v-card-title class="text-body-1 font-weight-medium pa-3 pb-0">
            거리 (km)
          </v-card-title>
          <v-card-text class="pa-3 pt-1">
            <svg
              :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
              width="100%"
              :height="svgHeight"
              role="img"
              aria-label="기간별 거리 바 차트"
            >
              <!-- Y축 가이드라인 -->
              <line
                v-for="guide in yGuides"
                :key="guide.y"
                :x1="paddingLeft"
                :y1="guide.y"
                :x2="svgWidth - paddingRight"
                :y2="guide.y"
                stroke="#e0e0e0"
                stroke-width="1"
              />
              <!-- Y축 레이블 -->
              <text
                v-for="guide in yGuides"
                :key="`label-${guide.y}`"
                :x="paddingLeft - 6"
                :y="guide.y + 4"
                text-anchor="end"
                font-size="10"
                fill="#9e9e9e"
              >
                {{ guide.label }}
              </text>

              <!-- 막대 -->
              <g v-for="(item, i) in store.data" :key="i">
                <rect
                  :x="barX(i)"
                  :y="barY(item.total_distance)"
                  :width="barWidth"
                  :height="barH(item.total_distance)"
                  :fill="barColor"
                  rx="3"
                  class="chart-bar"
                >
                  <title>{{ item.period_label }}: {{ item.total_distance.toFixed(1) }} km ({{ item.activity_count }}회)</title>
                </rect>
                <!-- 막대 위 수치 -->
                <text
                  v-if="barH(item.total_distance) > 14"
                  :x="barX(i) + barWidth / 2"
                  :y="barY(item.total_distance) - 4"
                  text-anchor="middle"
                  font-size="10"
                  :fill="barColor"
                  font-weight="600"
                >
                  {{ item.total_distance.toFixed(1) }}
                </text>
                <!-- X축 레이블 -->
                <text
                  :x="barX(i) + barWidth / 2"
                  :y="chartBottom + 14"
                  text-anchor="middle"
                  font-size="10"
                  fill="#757575"
                >
                  {{ shortLabel(item.period_label) }}
                </text>
              </g>
            </svg>
          </v-card-text>
        </v-card>

        <!-- 상세 테이블 -->
        <v-card variant="outlined">
          <v-card-title class="text-body-1 font-weight-medium pa-3 pb-0">상세 데이터</v-card-title>
          <v-data-table
            :headers="tableHeaders"
            :items="tableRows"
            density="compact"
            hide-default-footer
            :items-per-page="-1"
          />
        </v-card>
      </template>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useStatisticsStore } from '@/stores/statistics'
import { formatTime, formatPace } from '@/lib/format'

const store = useStatisticsStore()

// ── 요약 집계 ──────────────────────────────────────────────────────────────
const totalDistance = computed(() => {
  const km = store.data.reduce((s, d) => s + d.total_distance, 0)
  return `${km.toFixed(1)} km`
})

const totalActivities = computed(() => store.data.reduce((s, d) => s + d.activity_count, 0))

const totalTime = computed(() => {
  const sec = store.data.reduce((s, d) => s + d.total_moving_time, 0)
  return formatTime(sec)
})

const avgPace = computed(() => {
  const totalDistKm = store.data.reduce((s, d) => s + d.total_distance, 0)
  const totalSec = store.data.reduce((s, d) => s + d.total_moving_time, 0)
  if (totalDistKm <= 0) return '-'
  return formatPace(totalSec / totalDistKm)
})

// ── SVG 차트 ───────────────────────────────────────────────────────────────
const svgWidth = 600
const svgHeight = 200
const paddingLeft = 36
const paddingRight = 12
const paddingTop = 20
const paddingBottom = 24
const chartBottom = svgHeight - paddingBottom
const chartHeight = chartBottom - paddingTop
const barColor = '#e64a19'

const maxDistance = computed(() =>
  Math.max(...store.data.map((d) => d.total_distance), 0.1),
)

const barSlotWidth = computed(() => {
  const count = store.data.length || 1
  return (svgWidth - paddingLeft - paddingRight) / count
})

const barWidth = computed(() => Math.max(barSlotWidth.value * 0.6, 4))

function barX(i: number): number {
  return paddingLeft + i * barSlotWidth.value + (barSlotWidth.value - barWidth.value) / 2
}

function barH(dist: number): number {
  return (dist / maxDistance.value) * chartHeight
}

function barY(dist: number): number {
  return chartBottom - barH(dist)
}

// Y축 가이드라인: 0 / 50% / 100%
const yGuides = computed(() => {
  const max = maxDistance.value
  return [
    { y: chartBottom, label: '0' },
    { y: chartBottom - chartHeight / 2, label: (max / 2).toFixed(0) },
    { y: paddingTop, label: max.toFixed(0) },
  ]
})

function shortLabel(label: string): string {
  // "2026년 4월" → "4월", "2026년 18주차" → "18주", "2026년" → "2026"
  const monthMatch = label.match(/(\d+)월$/)
  if (monthMatch) return monthMatch[1] + '월'
  const weekMatch = label.match(/(\d+)주차$/)
  if (weekMatch) return weekMatch[1] + '주'
  const yearMatch = label.match(/^(\d+)년$/)
  if (yearMatch) return yearMatch[1] ?? label
  return label
}

// ── 테이블 ─────────────────────────────────────────────────────────────────
const tableHeaders = [
  { title: '기간', key: 'label', sortable: false },
  { title: '거리', key: 'distance', sortable: false },
  { title: '횟수', key: 'count', sortable: false },
  { title: '시간', key: 'time', sortable: false },
  { title: '평균 페이스', key: 'pace', sortable: false },
  { title: '평균 심박', key: 'hr', sortable: false },
  { title: '총 고도', key: 'elevation', sortable: false },
]

const tableRows = computed(() =>
  store.data.map((d) => ({
    label: d.period_label,
    distance: `${d.total_distance.toFixed(1)} km`,
    count: `${d.activity_count}회`,
    time: formatTime(d.total_moving_time),
    pace: formatPace(d.avg_pace_sec_per_km),
    hr: d.avg_heartrate ? `${d.avg_heartrate.toFixed(0)} bpm` : '-',
    elevation: `${d.total_elevation_gain.toFixed(0)} m`,
  })),
)

onMounted(() => store.loadStats())
</script>

<style scoped>
.chart-bar {
  cursor: default;
  transition: opacity 0.15s;
}
.chart-bar:hover {
  opacity: 0.75;
}
</style>
