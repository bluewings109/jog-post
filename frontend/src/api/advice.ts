import apiClient from './client'

export interface AdviceHistory {
  id: number
  activity_id: number | null
  response_text: string | null
  model_used: string | null
  created_at: string
}

export const fetchAdviceHistory = () =>
  apiClient.get<AdviceHistory[]>('/advice/history')

export const getAdviceStreamUrl = (activityId: number) =>
  `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/advice/activity/${activityId}`

export const getGeneralAdviceStreamUrl = () =>
  `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/advice/general`
