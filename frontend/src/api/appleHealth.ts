import apiClient from './client'

export interface AppleHealthConnectResponse {
  webhook_secret: string
  webhook_url: string
}

export const connectAppleHealth = () =>
  apiClient.post<AppleHealthConnectResponse>('/auth/apple-health/connect')

export const disconnectAppleHealth = () =>
  apiClient.delete('/auth/apple-health/disconnect')
