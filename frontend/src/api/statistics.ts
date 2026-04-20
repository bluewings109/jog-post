import apiClient from './client'

export interface PeriodStatsItem {
  period_label: string
  period_start: string
  activity_count: number
  total_distance: number
  total_moving_time: number
  avg_pace_sec_per_km: number | null
  avg_heartrate: number | null
  total_elevation_gain: number
}

export interface WeeklyStatsResponse {
  year: number
  month: number
  weeks: PeriodStatsItem[]
}

export interface MonthlyStatsResponse {
  year: number
  months: PeriodStatsItem[]
}

export interface YearlyStatsResponse {
  years: PeriodStatsItem[]
}

export const fetchWeeklyStats = (year: number, month: number) =>
  apiClient.get<WeeklyStatsResponse>('/statistics/weekly', { params: { year, month } })

export const fetchMonthlyStats = (year: number) =>
  apiClient.get<MonthlyStatsResponse>('/statistics/monthly', { params: { year } })

export const fetchYearlyStats = () => apiClient.get<YearlyStatsResponse>('/statistics/yearly')
