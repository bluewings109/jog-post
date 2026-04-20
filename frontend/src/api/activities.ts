import apiClient from './client'

export interface Activity {
  id: number
  strava_id: number
  name: string | null
  sport_type: string | null
  start_date: string
  start_date_local: string
  timezone: string | null
  distance: number | null
  moving_time: number | null
  elapsed_time: number | null
  total_elevation_gain: number | null
  average_speed: number | null
  max_speed: number | null
  average_heartrate: number | null
  max_heartrate: number | null
  average_cadence: number | null
  calories: number | null
  suffer_score: number | null
  summary_polyline: string | null
  achievement_count: number
  kudos_count: number
  pr_count: number
  trainer: boolean
  commute: boolean
  average_pace_sec_per_km: number | null
}

export interface SplitMetric {
  split: number
  distance: number | null
  elapsed_time: number | null
  moving_time: number | null
  average_speed: number | null
  average_heartrate: number | null
  pace_zone: number | null
  elevation_difference: number | null
}

export interface ActivityDetail extends Activity {
  laps: Lap[]
  splits_metric: SplitMetric[]
}

export interface Lap {
  id: number
  strava_id: number
  lap_index: number
  name: string | null
  elapsed_time: number | null
  moving_time: number | null
  distance: number | null
  average_speed: number | null
  max_speed: number | null
  average_cadence: number | null
  average_heartrate: number | null
  max_heartrate: number | null
  total_elevation_gain: number | null
  pace_zone: number | null
}

export interface ActivitiesResponse {
  items: Activity[]
  total: number
  page: number
  per_page: number
}

export const fetchActivities = (page = 1, perPage = 20, startDate?: string, endDate?: string) =>
  apiClient.get<ActivitiesResponse>('/activities', {
    params: { page, per_page: perPage, start_date: startDate, end_date: endDate },
  })

export const fetchActivity = (id: number) =>
  apiClient.get<ActivityDetail>(`/activities/${id}`)
