<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4" class="text-center">
        <h1 class="text-h3 font-weight-bold mb-2">JOG-POST</h1>
        <p class="text-subtitle-1 text-medium-emphasis mb-8">
          달리기 기록을 자동으로 수집하고 AI 코치의 조언을 받아보세요.
        </p>
        <v-btn
          color="deep-orange"
          size="large"
          :href="`${apiBase}/auth/strava/login`"
          prepend-icon="mdi-run"
        >
          Strava로 시작하기
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
</script>
