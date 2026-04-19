/** 초 → "mm:ss" 형식 */
export function formatTime(seconds: number | null | undefined): string {
  if (seconds == null) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

/** 미터 → "N.NN km" */
export function formatDistance(meters: number | null | undefined): string {
  if (meters == null) return '-'
  return `${(meters / 1000).toFixed(2)} km`
}

/** 초/km → "mm:ss /km" */
export function formatPace(secPerKm: number | null | undefined): string {
  if (secPerKm == null) return '-'
  const m = Math.floor(secPerKm / 60)
  const s = Math.round(secPerKm % 60)
  return `${m}:${String(s).padStart(2, '0')} /km`
}

/** ISO 날짜 문자열 → 로컬 날짜 표시 */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })
}

/** bpm 숫자 표시 */
export function formatHR(bpm: number | null | undefined): string {
  if (bpm == null) return '-'
  return `${Math.round(bpm)} bpm`
}

/** 고도 m 표시 */
export function formatElevation(m: number | null | undefined): string {
  if (m == null) return '-'
  return `${Math.round(m)} m`
}

/** 심박수에 따른 색상 클래스 (5존 기준) */
export function hrColor(bpm: number | null | undefined): string {
  if (!bpm) return ''
  if (bpm < 114) return 'hr-z1'
  if (bpm < 152) return 'hr-z2'
  if (bpm < 171) return 'hr-z3'
  if (bpm < 190) return 'hr-z4'
  return 'hr-z5'
}
