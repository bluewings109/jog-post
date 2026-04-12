import apiClient from './client'

export interface Activity {
  id: number
  strava_id: number
  name: string | null
  sport_type: string | null
  start_date: string
  distance: number | null
  moving_time: number | null
  elapsed_time: number | null
  total_elevation_gain: number | null
  average_speed: number | null
  average_heartrate: number | null
  summary_polyline: string | null
}

export interface ActivityDetail extends Activity {
  laps: Lap[]
  calories: number | null
  suffer_score: number | null
  average_cadence: number | null
  max_heartrate: number | null
}

export interface Lap {
  id: number
  lap_index: number
  distance: number | null
  moving_time: number | null
  average_speed: number | null
  average_heartrate: number | null
}

export interface ActivitiesResponse {
  items: Activity[]
  total: number
  page: number
  per_page: number
}

export const fetchActivities = (page = 1, perPage = 20) =>
  apiClient.get<ActivitiesResponse>('/activities', { params: { page, per_page: perPage } })

export const fetchActivity = (id: number) =>
  apiClient.get<ActivityDetail>(`/activities/${id}`)
