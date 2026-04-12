<template>
  <v-container max-width="760">
    <h1 class="text-h5 font-weight-bold mb-2">AI 달리기 코치</h1>
    <p class="text-body-2 text-medium-emphasis mb-6">
      최근 운동 기록을 분석하고 훈련 개선을 위한 맞춤 조언을 받아보세요.
    </p>

    <!-- 종합 조언 -->
    <v-card rounded="lg" elevation="2" class="mb-6">
      <v-card-text class="pa-5">
        <div class="text-subtitle-1 font-weight-bold mb-1">종합 훈련 분석</div>
        <div class="text-caption text-medium-emphasis mb-4">최근 4주 활동 기반</div>
        <AdviceChat stream-url="/advice/general" />
      </v-card-text>
    </v-card>

    <!-- 최근 활동 목록 + 개별 조언 -->
    <div class="text-subtitle-2 font-weight-medium mb-3">활동별 조언</div>

    <v-progress-linear v-if="activitiesStore.loading" indeterminate color="primary" class="mb-4" />

    <div v-if="!activitiesStore.loading && activitiesStore.activities.length === 0" class="text-center py-8 text-medium-emphasis">
      <v-icon size="48" class="mb-2">mdi-run</v-icon>
      <div>활동이 없습니다. 먼저 Strava에서 동기화하세요.</div>
    </div>

    <v-expansion-panels v-else variant="accordion" class="rounded-lg">
      <v-expansion-panel
        v-for="a in activitiesStore.activities.slice(0, 10)"
        :key="a.id"
        rounded="lg"
      >
        <v-expansion-panel-title>
          <div class="d-flex align-center justify-space-between w-100 pr-2">
            <span class="text-body-2 font-weight-medium">{{ a.name ?? '달리기' }}</span>
            <div class="d-flex gap-2 text-caption text-medium-emphasis">
              <span>{{ formatDistance(a.distance) }}</span>
              <span>{{ formatPace(a.average_pace_sec_per_km) }}</span>
              <span>{{ formatDate(a.start_date_local) }}</span>
            </div>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <AdviceChat :stream-url="`/advice/activity/${a.id}`" />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- 조언 히스토리 -->
    <div class="text-subtitle-2 font-weight-medium mt-8 mb-3">과거 조언 기록</div>

    <v-progress-linear v-if="historyLoading" indeterminate color="primary" class="mb-3" />

    <div v-if="!historyLoading && history.length === 0" class="text-caption text-medium-emphasis">
      아직 조언 기록이 없습니다.
    </div>

    <v-list v-else density="compact" lines="two">
      <v-list-item
        v-for="item in history"
        :key="item.id"
        :subtitle="item.response_text?.slice(0, 120) + '…'"
        class="mb-1 rounded-lg"
      >
        <template #title>
          <span class="text-caption text-medium-emphasis">
            {{ new Date(item.created_at).toLocaleDateString('ko-KR') }}
            {{ item.activity_id ? `· 활동 #${item.activity_id}` : '· 종합' }}
          </span>
        </template>
      </v-list-item>
    </v-list>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useActivitiesStore } from '@/stores/activities'
import AdviceChat from '@/components/AdviceChat.vue'
import { fetchAdviceHistory } from '@/api/advice'
import type { AdviceHistoryItem } from '@/api/advice'
import { formatDate, formatDistance, formatPace } from '@/lib/format'

const activitiesStore = useActivitiesStore()
const history = ref<AdviceHistoryItem[]>([])
const historyLoading = ref(false)

async function loadHistory() {
  historyLoading.value = true
  try {
    const { data } = await fetchAdviceHistory()
    history.value = data.items
  } finally {
    historyLoading.value = false
  }
}

onMounted(async () => {
  if (activitiesStore.activities.length === 0) {
    activitiesStore.loadActivities(1, 10)
  }
  await loadHistory()
})
</script>
