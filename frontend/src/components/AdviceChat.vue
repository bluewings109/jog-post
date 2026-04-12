<template>
  <div class="advice-chat">
    <!-- 헤더 + 실행 버튼 -->
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="text-subtitle-2 font-weight-medium">
        <v-icon size="18" color="primary" class="mr-1">mdi-robot-outline</v-icon>
        AI 달리기 코치
      </div>
      <v-btn
        :disabled="streaming"
        :loading="streaming"
        size="small"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-play"
        @click="startStream"
      >
        조언 받기
      </v-btn>
    </div>

    <!-- 스트리밍 / 결과 표시 -->
    <v-card v-if="text || streaming" rounded="lg" variant="tonal" color="surface-variant" class="pa-4">
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="advice-text" v-html="renderedMarkdown" />
      <span v-if="streaming" class="cursor-blink">▋</span>
    </v-card>

    <v-alert v-if="errorMsg" type="error" class="mt-3" closable @click:close="errorMsg = ''">
      {{ errorMsg }}
    </v-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { streamAdvice } from '@/api/advice'

// 간단한 마크다운 렌더러 (외부 라이브러리 없이)
function simpleMarkdown(md: string): string {
  return md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^\| (.+) \|$/gm, (line) => {
      const cells = line
        .slice(2, -2)
        .split(' | ')
        .map((c) => `<td>${c}</td>`)
        .join('')
      return `<tr>${cells}</tr>`
    })
    .replace(/(<tr>.*<\/tr>\n?)+/gs, (tbl) => `<table>${tbl}</table>`)
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/gs, (list) => `<ul>${list}</ul>`)
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[htuplo])(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '')
}

const props = defineProps<{
  /** '/advice/activity/{id}' 또는 '/advice/general' */
  streamUrl: string
}>()

const text = ref('')
const streaming = ref(false)
const errorMsg = ref('')
let abortFn: (() => void) | null = null

const renderedMarkdown = computed(() => simpleMarkdown(text.value))

function startStream() {
  if (streaming.value) return
  text.value = ''
  errorMsg.value = ''
  streaming.value = true

  abortFn = streamAdvice(
    props.streamUrl,
    (token) => {
      text.value += token
    },
    () => {
      streaming.value = false
    },
    (err) => {
      streaming.value = false
      errorMsg.value = err instanceof Error ? err.message : '조언을 불러오지 못했습니다.'
    },
  )
}

onBeforeUnmount(() => {
  abortFn?.()
})
</script>

<style scoped>
.advice-text :deep(h1),
.advice-text :deep(h2),
.advice-text :deep(h3) {
  margin: 0.6em 0 0.3em;
  font-weight: 600;
}

.advice-text :deep(ul) {
  padding-left: 1.4em;
  margin: 0.4em 0;
}

.advice-text :deep(li) {
  margin-bottom: 0.2em;
}

.advice-text :deep(table) {
  border-collapse: collapse;
  margin: 0.6em 0;
  font-size: 0.875rem;
}

.advice-text :deep(td) {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  padding: 4px 8px;
}

.advice-text :deep(code) {
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 4px;
  padding: 1px 4px;
  font-size: 0.85em;
}

.advice-text :deep(p) {
  margin: 0.4em 0;
  line-height: 1.7;
}

.cursor-blink {
  animation: blink 0.7s step-end infinite;
  opacity: 0.7;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>
