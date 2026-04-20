<template>
  <v-container max-width="600" class="py-8">
    <v-card v-if="auth.user" rounded="lg" elevation="2">
      <v-card-title class="pa-6 pb-2 text-h6">프로필 설정</v-card-title>

      <v-card-text class="pa-6">
        <!-- 사용자 기본 정보 -->
        <div class="d-flex align-center ga-4 mb-6">
          <v-avatar size="64">
            <v-img v-if="auth.user.picture" :src="auth.user.picture" :alt="auth.user.name ?? ''" />
            <v-icon v-else size="40">mdi-account-circle</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6">{{ auth.user.name ?? '이름 없음' }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ auth.user.email }}</div>
          </div>
        </div>

        <v-divider class="mb-6" />

        <!-- 공개 설정 -->
        <div class="mb-4">
          <div class="text-subtitle-1 font-weight-medium mb-1">통계 공개 설정</div>
          <div class="text-body-2 text-medium-emphasis mb-4">
            공개로 설정하면 다른 사람이 내 달리기 통계를 볼 수 있습니다.
          </div>
          <v-switch
            v-model="isPublic"
            :label="isPublic ? '공개' : '비공개'"
            color="deep-orange-darken-2"
            hide-details
            :loading="saving"
            @update:model-value="onToggle"
          />
        </div>

        <!-- 공개 URL -->
        <v-expand-transition>
          <div v-if="isPublic">
            <v-divider class="mb-4" />
            <div class="text-subtitle-2 mb-2">공개 프로필 URL</div>
            <div class="d-flex align-center ga-2">
              <v-text-field
                :model-value="publicUrl"
                readonly
                density="compact"
                variant="outlined"
                hide-details
              />
              <v-btn
                icon="mdi-content-copy"
                variant="tonal"
                size="small"
                @click="copyUrl"
              />
            </div>
            <v-btn
              :to="{ name: 'public-profile', params: { userId: auth.user.id } }"
              variant="text"
              color="deep-orange-darken-2"
              size="small"
              class="mt-2 px-0"
              append-icon="mdi-open-in-new"
            >
              공개 페이지 보기
            </v-btn>
          </div>
        </v-expand-transition>
      </v-card-text>
    </v-card>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="2500" location="bottom">
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isPublic = ref(false)
const saving = ref(false)
const snackbar = ref({ show: false, message: '', color: 'success' })

const publicUrl = computed(() => {
  if (!auth.user) return ''
  return `${window.location.origin}/public/${auth.user.id}`
})

onMounted(() => {
  isPublic.value = auth.user?.is_public ?? false
})

async function onToggle(value: boolean | null) {
  saving.value = true
  try {
    await auth.updatePublicSetting(value ?? false)
    snackbar.value = {
      show: true,
      message: (value ? '공개' : '비공개') + '로 설정되었습니다.',
      color: 'success',
    }
  } catch {
    isPublic.value = !value
    snackbar.value = { show: true, message: '설정 변경에 실패했습니다.', color: 'error' }
  } finally {
    saving.value = false
  }
}

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(publicUrl.value)
    snackbar.value = { show: true, message: 'URL이 복사되었습니다.', color: 'success' }
  } catch {
    snackbar.value = { show: true, message: 'URL 복사에 실패했습니다.', color: 'error' }
  }
}
</script>
