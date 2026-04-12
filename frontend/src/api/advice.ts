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
  const baseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

  fetch(`${baseUrl}/api/v1${url}`, {
    method: 'POST',
    credentials: 'include',
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.ok) {
        onError(new Error(`HTTP ${resp.status}`))
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
      if ((err as Error).name !== 'AbortError') onError(err)
    })

  return () => controller.abort()
}
