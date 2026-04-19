import apiClient from './client'

export interface AdviceHistoryItem {
  id: number
  activity_id: number | null
  prompt_context: string
  response_text: string | null
  model_used: string | null
  created_at: string
}

export interface AdviceHistoryResponse {
  items: AdviceHistoryItem[]
  total: number
}

export const fetchAdviceHistory = (page = 1, perPage = 10) =>
  apiClient.get<AdviceHistoryResponse>('/advice/history', {
    params: { page, per_page: perPage },
  })

/**
 * SSE 스트리밍으로 조언을 받는다.
 * @param url  '/advice/activity/{id}' 또는 '/advice/general'
 * @param onToken 토큰이 도착할 때마다 호출
 * @param onDone 스트림 완료 시 호출
 * @param onError 에러 발생 시 호출
 * @returns 스트림을 중단하는 abort 함수
 */
export function streamAdvice(
  url: string,
  onToken: (text: string) => void,
  onDone: () => void,
  onError: (err: unknown) => void,
): () => void {
  const controller = new AbortController()
  // VITE_API_URL이 없으면 같은 도메인(상대 경로) 사용
  const baseUrl = import.meta.env.VITE_API_URL ?? ''

  fetch(`${baseUrl}/api/v1${url}`, {
    method: 'POST',
    credentials: 'include',
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const messages: Record<number, string> = {
          401: '로그인이 필요합니다. 페이지를 새로고침 후 다시 시도해주세요.',
          403: '접근 권한이 없습니다.',
          404: '활동 정보를 찾을 수 없습니다.',
          429: 'AI 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.',
          500: 'AI 서버에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
          502: 'AI 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.',
          503: 'AI 서비스가 설정되지 않았습니다. LLM_PROVIDER와 LLM_API_KEY를 확인해주세요.',
        }
        onError(new Error(messages[resp.status] ?? `오류가 발생했습니다. (${resp.status})`))
        return
      }
      const reader = resp.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (payload === '[DONE]') {
            onDone()
            return
          }
          try {
            const parsed = JSON.parse(payload) as { text: string }
            onToken(parsed.text)
          } catch {
            // skip malformed lines
          }
        }
      }
      onDone()
    })
    .catch((err) => {
      if ((err as Error).name !== 'AbortError') {
        onError(new Error('AI 서비스에 연결할 수 없습니다. 네트워크 상태를 확인하고 다시 시도해주세요.'))
      }
    })

  return () => controller.abort()
}
