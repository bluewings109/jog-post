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

      <!-- 랩 -->
      <template v-if="store.currentActivity.laps.length > 0">
        <div class="text-subtitle-2 font-weight-medium mb-2">
          랩 ({{ store.currentActivity.laps.length }})
        </div>
        <v-card rounded="lg" elevation="1" class="mb-6">
          <LapTable :laps="store.currentActivity.laps" />
        </v-card>
      </template>

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
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActivitiesStore } from '@/stores/activities'
import ActivityStats from '@/components/ActivityStats.vue'
import LapTable from '@/components/LapTable.vue'
import RouteMap from '@/components/RouteMap.vue'
import { formatDate } from '@/lib/format'

const route = useRoute()
const router = useRouter()
const store = useActivitiesStore()

onMounted(() => store.loadActivity(Number(route.params.id)))
</script>
