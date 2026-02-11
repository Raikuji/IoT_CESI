<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6 flex-wrap ga-3 page-header">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Dashboard</h1>
        <p class="text-body-2 text-medium-emphasis">
          Bâtiment Orion - Campus CESI Nancy
        </p>
      </div>
      <v-chip color="primary" variant="tonal" size="large">
        <v-icon start class="pulse">mdi-circle</v-icon>
        Live
      </v-chip>
    </div>

    <!-- Grille des capteurs par étage -->
    <div v-if="floorGroups.length">
      <v-card
        v-for="floor in floorGroups"
        :key="floor.id"
        color="surface"
        class="floor-card mb-6"
      >
        <v-card-title class="d-flex align-center">
          <v-icon start>mdi-floor-plan</v-icon>
          {{ floor.name }}
        </v-card-title>
        <v-card-text>
          <div class="sensor-row">
            <v-card
              v-for="sensor in getFloorSensors(floor)"
              :key="sensor.id"
              class="sensor-tile"
              variant="flat"
              @click="openEnergyDialog(sensor, sensor.room)"
            >
              <div class="sensor-tile-content">
                <v-avatar :color="getSensorColor(sensor.type)" variant="tonal" size="44">
                  <v-icon size="20">{{ getSensorIcon(sensor.type) }}</v-icon>
                </v-avatar>
                <div class="sensor-tile-body">
                  <div class="sensor-tile-value" :style="{ color: getSensorValueColor(sensor) }">
                    {{ formatValue(sensor.value, sensor.type) }}
                    <span class="text-caption text-medium-emphasis">{{ getSensorUnit(sensor.type) }}</span>
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ getSensorLabel(sensor.type) }}
                  </div>
                  <div class="mt-2 d-flex align-center ga-1">
                    <v-chip size="x-small" variant="tonal">
                      {{ sensor.name || sensor.type }}
                    </v-chip>
                  </div>
                </div>
                <span :class="['status-dot', getSensorStatus(sensor)]"></span>
              </div>
            </v-card>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <v-card v-else class="text-center pa-8" color="surface">
      <v-icon size="64" color="grey">mdi-office-building-outline</v-icon>
      <h3 class="mt-4 text-h6">Aucun capteur affiché</h3>
      <p class="text-body-2 text-medium-emphasis mt-2">
        Les salles apparaîtront ici dès qu'elles contiennent des capteurs placés.
      </p>
    </v-card>

    <!-- KPI Cards Row -->
    <v-row class="mb-6">
      <v-col cols="12" lg="3">
        <v-card color="surface" class="h-100">
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-h4 font-weight-bold text-primary">
                  {{ averageTemperature.toFixed(1) }}°C
                </div>
                <div class="text-caption text-medium-emphasis">Température moyenne</div>
              </div>
              <v-avatar size="56" color="primary" variant="tonal">
                <v-icon size="28">mdi-thermometer</v-icon>
              </v-avatar>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" lg="3">
        <v-card color="surface" class="h-100">
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-h4 font-weight-bold" :style="{ color: activityRate >= 80 ? '#4CAF50' : activityRate >= 50 ? '#FF9800' : '#F44336' }">
                  {{ activityRate }}%
                </div>
                <div class="text-caption text-medium-emphasis">Activité capteurs</div>
              </div>
              <v-avatar size="56" :color="activityRate >= 80 ? 'success' : activityRate >= 50 ? 'warning' : 'error'" variant="tonal">
                <v-icon size="28">mdi-pulse</v-icon>
              </v-avatar>
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ activeRecentCount }}/{{ totalSensorsCount }} actifs
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" lg="3">
        <v-card color="surface" class="h-100">
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-h4 font-weight-bold text-success">
                  {{ energyEnabledRate }}%
                </div>
                <div class="text-caption text-medium-emphasis">Mode éco</div>
              </div>
              <v-avatar size="56" color="success" variant="tonal">
                <v-icon size="28">mdi-leaf</v-icon>
              </v-avatar>
            </div>
            <div class="text-caption text-medium-emphasis">
              Économie : {{ savingsRate }}%
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" lg="3">
        <v-card color="surface" class="h-100">
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-h4 font-weight-bold" :style="{ color: alertCount > 0 ? '#F44336' : '#4CAF50' }">
                  {{ alertCount }}
                </div>
                <div class="text-caption text-medium-emphasis">Alertes actives</div>
              </div>
              <v-avatar size="56" :color="alertCount > 0 ? 'error' : 'success'" variant="tonal">
                <v-icon size="28">{{ alertCount > 0 ? 'mdi-bell-alert' : 'mdi-check-circle' }}</v-icon>
              </v-avatar>
            </div>
            <div class="text-caption text-medium-emphasis">
              {{ alertCount > 0 ? 'Voir les alertes' : 'Tout va bien' }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Graphique température + Alertes -->
    <v-row class="mb-6">
      <v-col cols="12" lg="8">
        <v-card color="surface" class="h-100">
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-chart-line</v-icon>
            Évolution température
            <v-spacer />
            <v-btn-toggle v-model="chartPeriod" density="compact" variant="tonal" color="primary">
              <v-btn value="1h">1h</v-btn>
              <v-btn value="6h">6h</v-btn>
              <v-btn value="24h">24h</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text>
            <apexchart
              type="area"
              height="300"
              :options="chartOptions"
              :series="chartSeries"
            ></apexchart>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" lg="4">
        <v-card color="surface" class="h-100">
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-bell-alert</v-icon>
            Alertes actives
            <v-spacer />
            <v-chip size="small" :color="alertCount > 0 ? 'error' : 'success'" variant="tonal">
              {{ alertCount }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <v-list bg-color="transparent" density="compact">
              <v-list-item
                v-for="alert in recentAlerts"
                :key="alert.id"
                class="mb-2 rounded-lg"
              >
                <template v-slot:prepend>
                  <v-avatar :color="getSeverityColor(alert.severity)" variant="tonal">
                    <v-icon>{{ getSeverityIcon(alert.severity) }}</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>{{ alert.message }}</v-list-item-title>
                <v-list-item-subtitle>{{ formatDate(alert.created_at) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <div v-if="alertCount === 0" class="text-center py-6 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-check-circle</v-icon>
              <p class="text-body-2">Aucune alerte active</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useBuildingStore } from '@/stores/building'
import { useAlertsStore } from '@/stores/alerts'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const buildingStore = useBuildingStore()
const alertsStore = useAlertsStore()

const { floors, rooms, sensors: buildingSensors, energySettings } = storeToRefs(buildingStore)
const { activeAlerts } = storeToRefs(alertsStore)

const energyDialog = ref(false)
const selectedSensor = ref(null)
const selectedRoom = ref(null)
const energyForm = ref(buildingStore.getEnergySetting(null))

const energyProfileOptions = [
  { title: 'Normal', value: 'normal' },
  { title: 'Éco', value: 'eco' },
  { title: 'Nuit', value: 'night' }
]

const dayOptions = [
  { title: 'Lun', value: 0 },
  { title: 'Mar', value: 1 },
  { title: 'Mer', value: 2 },
  { title: 'Jeu', value: 3 },
  { title: 'Ven', value: 4 },
  { title: 'Sam', value: 5 },
  { title: 'Dim', value: 6 }
]

const sensorTypeOrder = ['temperature', 'humidity', 'co2', 'presence', 'pressure', 'light']

const chartPeriod = ref('6h')
const chartData = ref([])

const activityWindowMinutes = computed(() => {
  switch (chartPeriod.value) {
    case '1h':
      return 60
    case '24h':
      return 1440
    case '6h':
    default:
      return 360
  }
})

const alertCount = computed(() => activeAlerts.value.length)
const recentAlerts = computed(() => activeAlerts.value.slice(0, 5))

const totalSensorsCount = computed(() => buildingSensors.value.length)

const activeRecentCount = computed(() =>
  buildingSensors.value.filter(s => isSensorActiveRecent(s)).length
)

const inactiveRecentCount = computed(() =>
  Math.max(totalSensorsCount.value - activeRecentCount.value, 0)
)

const activityRate = computed(() =>
  totalSensorsCount.value ? Math.round((activeRecentCount.value / totalSensorsCount.value) * 100) : 0
)

const energyEnabledCount = computed(() => {
  return buildingSensors.value.filter(s => {
    const setting = energySettings.value?.[s.id] || buildingStore.getEnergySetting(s.id)
    return !!setting?.energy_enabled
  }).length
})

const energyDisabledCount = computed(() =>
  Math.max(totalSensorsCount.value - energyEnabledCount.value, 0)
)

const energyEnabledRate = computed(() =>
  totalSensorsCount.value ? Math.round((energyEnabledCount.value / totalSensorsCount.value) * 100) : 0
)

const consumptionRate = computed(() => {
  const baseline = totalSensorsCount.value || 0
  if (!baseline) return 0
  const sum = buildingSensors.value.reduce((acc, sensor) => {
    const setting = energySettings.value?.[sensor.id] || buildingStore.getEnergySetting(sensor.id)
    const profileWeight = setting?.profile === 'night' ? 0.4 : setting?.profile === 'eco' ? 0.6 : 1
    const interval = Number(setting?.refresh_interval || 60)
    const intervalWeight = Math.min(1, 60 / Math.max(interval, 1))
    const liveWeight = setting?.disable_live ? 0.85 : 1
    return acc + profileWeight * intervalWeight * liveWeight
  }, 0)
  return Math.round((sum / baseline) * 100)
})

const savingsRate = computed(() => {
  const baseline = totalSensorsCount.value || 0
  if (!baseline) return 0
  
  // Calcul de l'économie réelle basée sur les profils éco/nuit
  const savings = buildingSensors.value.reduce((acc, sensor) => {
    const setting = energySettings.value?.[sensor.id] || buildingStore.getEnergySetting(sensor.id)
    if (!setting?.energy_enabled) return acc
    
    // Si mode éco actif, on économise selon le profil
    const profileSaving = setting.profile === 'night' ? 0.6 : setting.profile === 'eco' ? 0.4 : 0
    const intervalSaving = setting.disable_live ? 0.15 : 0
    
    return acc + (profileSaving + intervalSaving)
  }, 0)
  
  return Math.round((savings / baseline) * 100)
})

const averageTemperature = computed(() => {
  const tempSensors = buildingSensors.value.filter(s => s.type === 'temperature' && s.value !== null)
  if (!tempSensors.length) return 0
  const sum = tempSensors.reduce((acc, s) => acc + Number(s.value), 0)
  return sum / tempSensors.length
})

const floorGroups = computed(() => {
  const roomsById = new Map(rooms.value.map(r => [r.id, r]))
  const sensorsByRoom = {}
  buildingSensors.value.forEach(sensor => {
    if (!sensor.roomId) return
    if (!roomsById.has(sensor.roomId)) return
    if (!sensorsByRoom[sensor.roomId]) sensorsByRoom[sensor.roomId] = []
    sensorsByRoom[sensor.roomId].push(sensor)
  })

  return [...floors.value]
    .sort((a, b) => (a.level ?? 0) - (b.level ?? 0))
    .map(floor => {
      const floorRooms = rooms.value
        .filter(r => r.floor === floor.id)
        .filter(r => (sensorsByRoom[r.id] || []).length)
        .sort((a, b) => a.id.localeCompare(b.id))
        .map(r => ({
          ...r,
          sensors: (sensorsByRoom[r.id] || []).sort((a, b) => {
            const aIdx = sensorTypeOrder.indexOf(a.type)
            const bIdx = sensorTypeOrder.indexOf(b.type)
            return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx)
          })
        }))

      return {
        ...floor,
        rooms: floorRooms
      }
    })
    .filter(floor => floor.rooms.length)
})

function getFloorSensors(floor) {
  if (!floor?.rooms?.length) return []
  return floor.rooms
    .flatMap(room => room.sensors.map(sensor => ({ ...sensor, room })))
    .sort((a, b) => {
      const aIdx = sensorTypeOrder.indexOf(a.type)
      const bIdx = sensorTypeOrder.indexOf(b.type)
      return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx)
    })
}

watch(buildingSensors, (sensors) => {
  const ids = sensors.map(s => s.id)
  buildingStore.ensureEnergySettings(ids)
}, { immediate: true })

watch(chartPeriod, () => {
  generateChartData()
})

function getSensorIcon(type) {
  const icons = {
    temperature: 'mdi-thermometer',
    humidity: 'mdi-water-percent',
    pressure: 'mdi-gauge',
    presence: 'mdi-motion-sensor',
    co2: 'mdi-molecule-co2',
    light: 'mdi-lightbulb'
  }
  return icons[type] || 'mdi-chip'
}

function getSensorColor(type) {
  const colors = {
    temperature: 'error',
    humidity: 'info',
    pressure: 'secondary',
    presence: 'success',
    co2: 'warning',
    light: 'amber'
  }
  return colors[type] || 'grey'
}

function getSensorLabel(type) {
  const labels = {
    temperature: 'Température',
    humidity: 'Humidité',
    pressure: 'Pression',
    presence: 'Présence',
    co2: 'CO2',
    light: 'Luminosité'
  }
  return labels[type] || 'Capteur'
}

function getSensorUnit(type) {
  const units = {
    temperature: '°C',
    humidity: '%',
    pressure: 'hPa',
    presence: '',
    co2: 'ppm',
    light: 'lx'
  }
  return units[type] || ''
}

function getSensorStatus(sensor) {
  return sensor?.status || 'offline'
}

function isSensorActiveRecent(sensor) {
  if (!sensor) return false
  if (sensor.status && sensor.status !== 'ok') return false
  if (!sensor.lastUpdate) return false
  const last = new Date(sensor.lastUpdate)
  if (Number.isNaN(last.getTime())) return false
  const diffMs = Date.now() - last.getTime()
  return diffMs <= activityWindowMinutes.value * 60 * 1000
}

function getSensorValueColor(sensor) {
  if (sensor?.type === 'presence') return sensor.value ? '#22c55e' : '#6b7280'
  return '#22c55e'
}

function formatValue(value, type) {
  if (value === null || value === undefined) return '--'
  if (type === 'presence') return value ? 'Oui' : 'Non'
  return Number(value).toFixed(1)
}

function getSeverityColor(severity) {
  const colors = { danger: 'error', warning: 'warning', info: 'info' }
  return colors[severity] || 'grey'
}

function getSeverityIcon(severity) {
  const icons = {
    danger: 'mdi-alert-circle',
    warning: 'mdi-alert',
    info: 'mdi-information'
  }
  return icons[severity] || 'mdi-bell'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: 'short'
  })
}

function generateChartData() {
  const now = Date.now()
  const data = []
  let totalMinutes
  let intervalMinutes
  switch (chartPeriod.value) {
    case '1h':
      totalMinutes = 60
      intervalMinutes = 1
      break
    case '6h':
      totalMinutes = 360
      intervalMinutes = 5
      break
    case '24h':
      totalMinutes = 1440
      intervalMinutes = 15
      break
    default:
      totalMinutes = 360
      intervalMinutes = 5
  }
  const points = Math.floor(totalMinutes / intervalMinutes)
  for (let i = points; i >= 0; i--) {
    data.push({
      x: now - i * intervalMinutes * 60000,
      y: 21 + Math.random() * 3
    })
  }
  chartData.value = data
}

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    toolbar: { show: false },
    background: 'transparent',
    animations: { enabled: true, easing: 'easeinout', speed: 800 }
  },
  colors: ['#ff6b6b'],
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 90, 100] }
  },
  stroke: { curve: 'smooth', width: 3 },
  grid: { borderColor: 'rgba(255, 255, 255, 0.1)', strokeDashArray: 4 },
  xaxis: { type: 'datetime', labels: { style: { colors: '#888' } } },
  yaxis: {
    labels: {
      style: { colors: '#888' },
      formatter: (val) => `${val.toFixed(1)}°C`
    }
  },
  tooltip: { theme: 'dark', x: { format: 'HH:mm:ss' } },
  dataLabels: { enabled: false }
}))

const chartSeries = computed(() => [{ name: 'Température', data: chartData.value }])

function isEcoActive(sensorId) {
  const setting = buildingStore.getEnergySetting(sensorId)
  return Boolean(setting.energy_enabled || setting.schedule_enabled)
}

async function openEnergyDialog(sensor, room) {
  selectedSensor.value = sensor
  selectedRoom.value = room
  const setting = await buildingStore.fetchSensorEnergySetting(sensor.id)
  energyForm.value = { ...setting }
  energyDialog.value = true
}

function applyEnergyProfile(profile) {
  const presets = {
    normal: { energy_enabled: false, refresh_interval: 60, disable_live: false },
    eco: { energy_enabled: true, refresh_interval: 120, disable_live: true },
    night: { energy_enabled: true, refresh_interval: 300, disable_live: true }
  }
  const preset = presets[profile] || presets.normal
  energyForm.value = {
    ...energyForm.value,
    profile,
    energy_enabled: preset.energy_enabled,
    refresh_interval: preset.refresh_interval,
    disable_live: preset.disable_live
  }
}

async function saveEnergySettings() {
  if (!selectedSensor.value) return
  const payload = {
    energy_enabled: energyForm.value.energy_enabled,
    refresh_interval: energyForm.value.refresh_interval,
    refresh_interval_night: energyForm.value.refresh_interval_night,
    disable_live: energyForm.value.disable_live,
    profile: energyForm.value.profile,
    schedule_enabled: energyForm.value.schedule_enabled,
    schedule_profile: energyForm.value.schedule_profile,
    schedule_days: energyForm.value.schedule_days,
    schedule_start: energyForm.value.schedule_start,
    schedule_end: energyForm.value.schedule_end
  }
  await buildingStore.updateSensorEnergySetting(selectedSensor.value.id, payload)
  energyDialog.value = false
}

onMounted(() => {
  generateChartData()
})
</script>

<style scoped>
.sensor-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 18px;
  align-items: stretch;
  overflow-x: auto;
  padding-bottom: 6px;
  scroll-snap-type: x mandatory;
}

.sensor-tile {
  padding: 18px 20px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  flex: 0 0 320px;
  min-width: 320px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  scroll-snap-align: start;
}

.sensor-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
}

.sensor-tile-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sensor-tile-body {
  flex: 1 1 auto;
}

.sensor-tile-value {
  font-size: 1.2rem;
  font-weight: 700;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #94a3b8;
  box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.15);
}

.status-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.18);
}

.status-dot.warning {
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.18);
}

.status-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.18);
}

.pulse {
  animation: pulse 1.2s infinite;
}

.page-header {
  padding: 4px 2px 10px;
}

.floor-card {
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: #ffffff;
  box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
