<template>
  <v-container max-width="860">
    <div class="d-flex align-center justify-space-between mb-4">
      <h1 class="text-h5 font-weight-bold">활동 목록</h1>
    </div>

    <!-- 기간 선택 -->
    <v-row align="center" justify="center" class="mb-4" no-gutters>
      <v-btn-toggle
        :model-value="store.viewMode"
        mandatory
        density="compact"
        color="deep-orange"
        class="mr-4"
        @update:model-value="store.setViewMode($event)"
      >
        <v-btn value="week" size="small">주별</v-btn>
        <v-btn value="month" size="small">월별</v-btn>
        <v-btn value="year" size="small">연별</v-btn>
      </v-btn-toggle>

      <v-btn icon="mdi-chevron-left" variant="text" density="compact" @click="store.prevPeriod()" />
      <span class="text-body-1 font-weight-medium mx-2" style="min-width: 120px; text-align: center">
        {{ store.periodLabel }}
      </span>
      <v-btn
        icon="mdi-chevron-right"
        variant="text"
        density="compact"
        :disabled="store.isCurrentPeriod"
        @click="store.nextPeriod()"
      />
    </v-row>

    <v-progress-linear v-if="store.loading" indeterminate color="primary" class="mb-4" />

    <template v-if="!store.loading">
      <div v-if="store.activities.length === 0" class="text-center py-12 text-medium-emphasis">
        <v-icon size="64" class="mb-3">mdi-run</v-icon>
        <div class="text-h6">{{ store.periodLabel }}에 활동이 없어요</div>
        <div class="text-body-2 mt-1">다른 기간을 선택하거나, 프로필에서 Apple Health 연동을 확인해보세요.</div>
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

const store = useActivitiesStore()
const page = ref(1)
const perPage = 20

const totalPages = computed(() => Math.ceil(store.total / perPage))

async function loadPage(p: number) {
  page.value = p
  await store.loadActivities(p, perPage)
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
