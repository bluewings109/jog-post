<template>
  <v-container max-width="860">
    <div class="d-flex align-center justify-space-between mb-4">
      <h1 class="text-h5 font-weight-bold">활동 목록</h1>
      <v-btn
        color="primary"
        variant="tonal"
        :loading="syncing"
        prepend-icon="mdi-sync"
        @click="syncActivities"
      >
        Strava 동기화
      </v-btn>
    </div>

    <v-alert
      v-if="syncMessage"
      :type="syncSuccess ? 'success' : 'error'"
      class="mb-4"
      closable
      @click:close="syncMessage = ''"
    >
      {{ syncMessage }}
    </v-alert>

    <v-progress-linear v-if="store.loading" indeterminate color="primary" class="mb-4" />

    <template v-if="!store.loading">
      <div v-if="store.activities.length === 0" class="text-center py-12 text-medium-emphasis">
        <v-icon size="64" class="mb-3">mdi-run</v-icon>
        <div class="text-h6">아직 활동이 없어요</div>
        <div class="text-body-2 mt-1">Strava 동기화 버튼을 눌러 불러오세요.</div>
      </div>

      <div v-else class="activity-grid">
        <ActivityCard v-for="a in store.activities" :key="a.id" :activity="a" />
      </div>

      <div v-if="totalPages > 1" class="d-flex justify-center mt-6">
        <v-pagination v-model="page" :length="totalPages" @update:model-value="loadPage" />
      </div>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useActivitiesStore } from '@/stores/activities'
import ActivityCard from '@/components/ActivityCard.vue'
import apiClient from '@/api/client'

const store = useActivitiesStore()
const page = ref(1)
const perPage = 20
const syncing = ref(false)
const syncMessage = ref('')
const syncSuccess = ref(true)

const totalPages = computed(() => Math.ceil(store.total / perPage))

async function loadPage(p: number) {
  page.value = p
  await store.loadActivities(p, perPage)
}

async function syncActivities() {
  syncing.value = true
  syncMessage.value = ''
  try {
    const { data } = await apiClient.post<{ synced: number }>('/activities/sync')
    syncSuccess.value = true
    syncMessage.value = `${data.synced}개 활동을 동기화했습니다.`
    await store.loadActivities(1, perPage)
    page.value = 1
  } catch {
    syncSuccess.value = false
    syncMessage.value = 'Strava 연동을 먼저 완료해주세요.'
  } finally {
    syncing.value = false
  }
}

onMounted(() => store.loadActivities(1, perPage))
</script>

<style scoped>
.activity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
</style>
