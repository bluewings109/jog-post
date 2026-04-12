<template>
  <v-container>
    <v-progress-circular v-if="store.loading" indeterminate />
    <template v-else-if="store.currentActivity">
      <h1 class="text-h5 mb-4">{{ store.currentActivity.name ?? '달리기' }}</h1>
      <p class="text-caption text-medium-emphasis mb-4">
        {{ formatDate(store.currentActivity.start_date) }}
      </p>
      <!-- Phase 4에서 상세 컴포넌트로 교체 예정 -->
      <pre class="text-caption">{{ JSON.stringify(store.currentActivity, null, 2) }}</pre>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useActivitiesStore } from '@/stores/activities'

const route = useRoute()
const store = useActivitiesStore()

onMounted(() => store.loadActivity(Number(route.params.id)))

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ko-KR')
}
</script>
