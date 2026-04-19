import axios from 'axios'

// VITE_API_URL이 설정되지 않으면 같은 도메인(상대 경로) 사용
const baseURL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL + '/api/v1'
  : '/api/v1'

const apiClient = axios.create({
  baseURL,
  withCredentials: true,
})

export default apiClient
