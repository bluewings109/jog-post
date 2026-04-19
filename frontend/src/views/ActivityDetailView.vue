<template>
  <v-container max-width="860">
    <v-progress-linear v-if="store.loading" indeterminate color="primary" class="mb-4" />

    <v-alert v-if="!store.loading && !store.currentActivity" type="warning" class="mt-4">
      활동을 찾을 수 없습니다.
    </v-alert>

    <template v-if="store.currentActivity">
      <div class="d-flex align-center mb-1">
        <v-btn icon="mdi-arrow-left" variant="text" size="small" @click="router.back()" />
        <span class="text-caption text-medium-emphasis ml-1">
          {{ formatDate(store.currentActivity.start_date_local) }}
        </span>
      </div>

      <h1 class="text-h5 font-weight-bold mb-4">
        {{ store.currentActivity.name ?? '달리기' }}
      </h1>

      <!-- 통계 -->
      <ActivityStats :activity="store.currentActivity" class="mb-6" />

      <!-- 지도 -->
      <template v-if="store.currentActivity.summary_polyline">
        <div class="text-subtitle-2 font-weight-medium mb-2">경로</div>
        <RouteMap :encoded-polyline="store.currentActivity.summary_polyline" class="mb-6" />
      </template>

      <!-- 구간/랩 탭 -->
      <template v-if="store.currentActivity.splits_metric.length > 0 || store.currentActivity.laps.length > 0">
        <v-tabs v-model="lapTab" density="compact" class="mb-2">
          <v-tab v-if="store.currentActivity.splits_metric.length > 0" value="splits">
            km 구간
          </v-tab>
          <v-tab v-if="store.currentActivity.laps.length > 0" value="laps">
            사용자 랩 ({{ store.currentActivity.laps.length }})
          </v-tab>
        </v-tabs>
        <v-card rounded="lg" elevation="1" class="mb-6">
          <v-window v-model="lapTab">
            <v-window-item value="splits">
              <SplitsTable :splits="store.currentActivity.splits_metric" />
            </v-window-item>
            <v-window-item value="laps">
              <LapTable :laps="store.currentActivity.laps" />
            </v-window-item>
          </v-window>
        </v-card>
      </template>

      <!-- AI 조언 -->
      <div class="text-subtitle-2 font-weight-medium mb-2">AI 조언</div>
      <v-card rounded="lg" elevation="1" class="mb-6 pa-4">
        <AdviceChat :stream-url="`/advice/activity/${store.currentActivity.id}`" />
      </v-card>

      <!-- 부가 정보 -->
      <v-row dense class="text-caption text-medium-emphasis">
        <v-col v-if="store.currentActivity.trainer" cols="auto">
          <v-chip size="x-small" prepend-icon="mdi-dumbbell">실내 트레이너</v-chip>
        </v-col>
        <v-col v-if="store.currentActivity.commute" cols="auto">
          <v-chip size="x-small" prepend-icon="mdi-bike">출퇴근</v-chip>
        </v-col>
        <v-col v-if="store.currentActivity.achievement_count > 0" cols="auto">
          <v-chip size="x-small" prepend-icon="mdi-trophy-outline">
            업적 {{ store.currentActivity.achievement_count }}
          </v-chip>
        </v-col>
        <v-col v-if="store.currentActivity.kudos_count > 0" cols="auto">
          <v-chip size="x-small" prepend-icon="mdi-thumb-up-outline">
            쿠도스 {{ store.currentActivity.kudos_count }}
          </v-chip>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActivitiesStore } from '@/stores/activities'
import ActivityStats from '@/components/ActivityStats.vue'
import AdviceChat from '@/components/AdviceChat.vue'
import LapTable from '@/components/LapTable.vue'
import SplitsTable from '@/components/SplitsTable.vue'
import RouteMap from '@/components/RouteMap.vue'
import { formatDate } from '@/lib/format'

const route = useRoute()
const router = useRouter()
const store = useActivitiesStore()

const hasSplits = computed(() => (store.currentActivity?.splits_metric?.length ?? 0) > 0)
const lapTab = ref<'splits' | 'laps'>('splits')

onMounted(async () => {
  await store.loadActivity(Number(route.params.id))
  lapTab.value = hasSplits.value ? 'splits' : 'laps'
})
</script>
