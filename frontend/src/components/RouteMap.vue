<template>
  <div ref="mapEl" class="route-map"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import polyline from '@mapbox/polyline'

const props = defineProps<{ encodedPolyline: string }>()

const mapEl = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let polylineLayer: L.Polyline | null = null

function initMap() {
  if (!mapEl.value) return

  map = L.map(mapEl.value, { zoomControl: true, attributionControl: false })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map)

  renderRoute(props.encodedPolyline)
}

function renderRoute(encoded: string) {
  if (!map || !encoded) return

  const latLngs = polyline.decode(encoded).map(([lat, lng]) => L.latLng(lat, lng))
  if (latLngs.length === 0) return

  if (polylineLayer) {
    polylineLayer.remove()
  }

  polylineLayer = L.polyline(latLngs, {
    color: '#FF5722',
    weight: 3,
    opacity: 0.85,
  }).addTo(map)

  // 시작/종료 마커
  const first = latLngs[0]
  const last = latLngs[latLngs.length - 1]
  if (first) L.circleMarker(first, { radius: 6, color: '#4CAF50', fillOpacity: 1, weight: 2 }).addTo(map!)
  if (last) L.circleMarker(last, { radius: 6, color: '#F44336', fillOpacity: 1, weight: 2 }).addTo(map!)

  map.fitBounds(polylineLayer.getBounds(), { padding: [16, 16] })
}

onMounted(() => {
  initMap()
})

watch(
  () => props.encodedPolyline,
  (val) => {
    renderRoute(val)
  },
)

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<style scoped>
.route-map {
  width: 100%;
  height: 320px;
  border-radius: 12px;
  overflow: hidden;
}
</style>
