import apiClient from './client'
import type { YearlyStatsResponse, MonthlyStatsResponse } from './statistics'

export interface PublicUser {
  id: number
  name: string | null
  picture: string | null
}

export const fetchPublicUser = (userId: number) =>
  apiClient.get<PublicUser>(`/public/users/${userId}`)

export const fetchPublicUserByEmail = (email: string) =>
  apiClient.get<PublicUser>('/public/users/lookup', { params: { email } })

export const fetchPublicYearlyStats = (userId: number) =>
  apiClient.get<YearlyStatsResponse>(`/public/users/${userId}/statistics/yearly`)

export const fetchPublicMonthlyStats = (userId: number, year: number) =>
  apiClient.get<MonthlyStatsResponse>(`/public/users/${userId}/statistics/monthly`, {
    params: { year },
  })
