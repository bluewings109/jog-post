<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" class="text-center">
        <v-icon size="72" color="deep-orange" class="mb-4">mdi-run-fast</v-icon>
        <h1 class="text-h3 font-weight-bold mb-2">JOG-POST</h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-8">
          달리기 기록을 자동으로 수집하고 AI 코치의 조언을 받아보세요.
        </p>

        <!-- 로그인 전 -->
        <template v-if="!authStore.user">
          <v-btn
            color="deep-orange"
            size="large"
            :href="`${apiBase}/api/v1/auth/google/login`"
            prepend-icon="mdi-google"
          >
            Google로 시작하기
          </v-btn>
        </template>

        <!-- 로그인 후 -->
        <template v-else>
          <v-row justify="center" class="gap-3">
            <v-col cols="auto">
              <v-btn color="primary" size="large" to="/activities" prepend-icon="mdi-run">
                내 활동 보기
              </v-btn>
            </v-col>
            <v-col v-if="!hasStrava" cols="auto">
              <v-btn
                color="deep-orange"
                size="large"
                variant="tonal"
                :href="`${apiBase}/api/v1/auth/strava/connect`"
                prepend-icon="mdi-link"
              >
                Strava 연동
              </v-btn>
            </v-col>
          </v-row>

          <v-alert v-if="!hasStrava" type="info" variant="tonal" class="mt-6 text-left">
            Strava를 연동하면 달리기가 끝날 때마다 자동으로 기록이 저장됩니다.
          </v-alert>
        </template>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const authStore = useAuthStore()

const hasStrava = computed(() =>
  authStore.user?.data_sources?.some((ds: { provider: string }) => ds.provider === 'strava'),
)
</script>
