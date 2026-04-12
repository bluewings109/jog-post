<template>
  <v-app>
    <v-app-bar color="deep-orange-darken-2" flat>
      <v-app-bar-title>
        <router-link to="/" class="text-white text-decoration-none font-weight-bold">
          JOG-POST
        </router-link>
      </v-app-bar-title>
      <template v-if="auth.isLoggedIn">
        <v-btn :to="{ name: 'activities' }" variant="text" color="white">기록</v-btn>
        <v-btn :to="{ name: 'advice' }" variant="text" color="white">AI 조언</v-btn>
        <v-btn variant="text" color="white" @click="auth.logout()">로그아웃</v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

onMounted(() => auth.fetchMe())
</script>
