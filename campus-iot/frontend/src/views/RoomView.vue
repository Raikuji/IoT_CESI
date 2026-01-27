<template>
  <div class="room-view">
    <!-- Header -->
    <div class="room-hero mb-8" :style="{ background: getRoomGradient }">
      <div class="hero-content">
        <v-btn
          icon
          variant="text"
          class="back-btn"
          @click="router.push('/building')"
        >
          <v-icon size="28">mdi-arrow-left</v-icon>
        </v-btn>
        <div class="room-info">
          <v-chip :color="getRoomTypeColor" variant="flat" class="mb-2">
            <v-icon start size="14">{{ getRoomTypeIcon }}</v-icon>
            {{ getRoomTypeLabel }}
          </v-chip>
          <h1 class="text-h3 font-weight-black mb-2">{{ room?.name || 'Salle' }}</h1>
          <p class="text-body-1 opacity-80">
            {{ room?.sensors?.length || 0 }} capteurs installés
          </p>
        </div>
      </div>
      <div class="hero-decoration"></div>
    </div>

    <v-row>
      <!-- Sensors Grid -->
      <v-col cols="12" lg="4">
        <v-card class="sensors-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-chip</v-icon>
            <span class="font-weight-bold">Capteurs</span>
            <v-spacer />
            <v-btn
              icon
              variant="text"
              size="small"
              @click="exportRoomData"
              :loading="exporting"
            >
              <v-icon>mdi-download</v-icon>
              <v-tooltip activator="parent" location="top">Exporter</v-tooltip>
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <v-list v-if="room?.sensors?.length" density="comfortable" class="sensors-list">
              <v-list-item
                v-for="sensor in room.sensors"
                :key="sensor.id"
                class="sensor-item"
                :class="{ active: selectedSensor?.id === sensor.id }"
                @click="selectSensor(sensor)"
              >
                <template v-slot:prepend>
                  <v-avatar :color="getSensorColor(sensor.type)" size="44">
                    <v-icon color="white">{{ getSensorIcon(sensor.type) }}</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-semibold">
                  {{ getSensorTypeName(sensor.type) }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <span class="sensor-value">{{ formatValue(sensor.value, sensor.type) }}</span>
                  <span class="sensor-unit">{{ sensor.unit }}</span>
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-chip
                    :color="sensor.status === 'online' ? 'success' : 'error'"
                    size="x-small"
                    variant="tonal"
                  >
                    {{ sensor.status === 'online' ? 'OK' : 'OFF' }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-12 text-medium-emphasis">
              <v-icon size="64" class="mb-4">mdi-chip-off</v-icon>
              <p class="text-body-1">Aucun capteur installé</p>
              <v-btn
                color="primary"
                variant="tonal"
                class="mt-4"
                @click="router.push('/building')"
              >
                Ajouter des capteurs
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Room Info -->
        <v-card class="info-card">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="info">mdi-information</v-icon>
            <span class="font-weight-bold">Informations</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-5">
            <v-list bg-color="transparent" density="compact">
              <v-list-item>
                <v-list-item-title class="text-medium-emphasis">Étage</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-semibold">{{ room?.floor || 'R+1' }}</span>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-medium-emphasis">Capacité</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-semibold">{{ room?.capacity || 0 }} places</span>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-medium-emphasis">Surface</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-semibold">{{ room?.area || 0 }} m²</span>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Charts -->
      <v-col cols="12" lg="8">
        <!-- Main Chart -->
        <v-card class="chart-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-chart-line</v-icon>
            <span class="font-weight-bold">
              Historique {{ selectedSensor ? getSensorTypeName(selectedSensor.type) : '' }}
            </span>
            <v-spacer />
            <v-btn-toggle
              v-model="chartPeriod"
              mandatory
              density="compact"
              variant="outlined"
              divided
            >
              <v-btn value="1h" size="small">1H</v-btn>
              <v-btn value="6h" size="small">6H</v-btn>
              <v-btn value="24h" size="small">24H</v-btn>
              <v-btn value="7d" size="small">7J</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-5">
            <div v-if="selectedSensor && chartData.length > 0" class="chart-container">
              <apexchart
                type="area"
                height="350"
                :options="chartOptions"
                :series="chartSeries"
              ></apexchart>
            </div>
            <div v-else class="text-center py-12 text-medium-emphasis">
              <v-icon size="64" class="mb-4">mdi-chart-line-variant</v-icon>
              <p class="text-body-1">
                {{ selectedSensor ? 'Aucune donnée disponible' : 'Sélectionnez un capteur' }}
              </p>
            </div>
          </v-card-text>
        </v-card>

        <!-- Stats Cards -->
        <v-row v-if="selectedSensor">
          <v-col cols="6" md="3">
            <v-card class="stat-card">
              <v-card-text class="text-center pa-4">
                <v-icon :color="getSensorColor(selectedSensor.type)" size="32" class="mb-2">
                  mdi-arrow-down
                </v-icon>
                <div class="stat-value">{{ stats.min }}</div>
                <div class="stat-label">Minimum</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" md="3">
            <v-card class="stat-card">
              <v-card-text class="text-center pa-4">
                <v-icon :color="getSensorColor(selectedSensor.type)" size="32" class="mb-2">
                  mdi-arrow-up
                </v-icon>
                <div class="stat-value">{{ stats.max }}</div>
                <div class="stat-label">Maximum</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" md="3">
            <v-card class="stat-card">
              <v-card-text class="text-center pa-4">
                <v-icon :color="getSensorColor(selectedSensor.type)" size="32" class="mb-2">
                  mdi-approximately-equal
                </v-icon>
                <div class="stat-value">{{ stats.avg }}</div>
                <div class="stat-label">Moyenne</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" md="3">
            <v-card class="stat-card">
              <v-card-text class="text-center pa-4">
                <v-icon :color="getSensorColor(selectedSensor.type)" size="32" class="mb-2">
                  mdi-counter
                </v-icon>
                <div class="stat-value">{{ stats.count }}</div>
                <div class="stat-label">Mesures</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Multi-sensor comparison -->
        <v-card v-if="room?.sensors?.length > 1" class="comparison-card mt-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="secondary">mdi-chart-multiple</v-icon>
            <span class="font-weight-bold">Comparaison</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-5">
            <div class="comparison-grid">
              <div
                v-for="sensor in room.sensors"
                :key="sensor.id"
                class="comparison-item"
                :style="{ borderColor: getSensorColor(sensor.type) }"
              >
                <div class="comparison-icon" :style="{ background: getSensorColor(sensor.type) }">
                  <v-icon color="white" size="20">{{ getSensorIcon(sensor.type) }}</v-icon>
                </div>
                <div class="comparison-data">
                  <div class="comparison-value">
                    {{ formatValue(sensor.value, sensor.type) }}
                    <span class="comparison-unit">{{ sensor.unit }}</span>
                  </div>
                  <div class="comparison-label">{{ getSensorTypeName(sensor.type) }}</div>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBuildingStore } from '@/stores/building'
import { useExport } from '@/composables/useExport'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const route = useRoute()
const router = useRouter()
const buildingStore = useBuildingStore()
const { exportToCSV, exporting } = useExport()

const roomId = computed(() => route.params.roomId)
const room = computed(() => buildingStore.getRoomById(roomId.value))
const selectedSensor = ref(null)
const chartPeriod = ref('6h')
const chartData = ref([])

// Room type styling
const roomTypes = {
  classroom: { color: '#3b82f6', icon: 'mdi-school', label: 'Salle de cours', gradient: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)' },
  lab: { color: '#8b5cf6', icon: 'mdi-flask', label: 'Laboratoire', gradient: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)' },
  meeting: { color: '#f59e0b', icon: 'mdi-account-group', label: 'Salle de réunion', gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' },
  office: { color: '#22c55e', icon: 'mdi-desk', label: 'Bureau', gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' },
  common: { color: '#06b6d4', icon: 'mdi-sofa', label: 'Espace commun', gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' },
  utility: { color: '#64748b', icon: 'mdi-tools', label: 'Local technique', gradient: 'linear-gradient(135deg, #64748b 0%, #475569 100%)' }
}

const sensorTypes = {
  temperature: { color: '#ef4444', icon: 'mdi-thermometer', name: 'Température' },
  humidity: { color: '#3b82f6', icon: 'mdi-water-percent', name: 'Humidité' },
  presence: { color: '#22c55e', icon: 'mdi-motion-sensor', name: 'Présence' },
  co2: { color: '#f59e0b', icon: 'mdi-molecule-co2', name: 'CO2' },
  light: { color: '#fbbf24', icon: 'mdi-lightbulb', name: 'Luminosité' }
}

const getRoomGradient = computed(() => roomTypes[room.value?.type]?.gradient || roomTypes.classroom.gradient)
const getRoomTypeColor = computed(() => roomTypes[room.value?.type]?.color || '#3b82f6')
const getRoomTypeIcon = computed(() => roomTypes[room.value?.type]?.icon || 'mdi-door')
const getRoomTypeLabel = computed(() => roomTypes[room.value?.type]?.label || 'Salle')

function getSensorColor(type) {
  return sensorTypes[type]?.color || '#64748b'
}

function getSensorIcon(type) {
  return sensorTypes[type]?.icon || 'mdi-chip'
}

function getSensorTypeName(type) {
  return sensorTypes[type]?.name || type
}

function formatValue(value, type) {
  if (value === null || value === undefined) return '--'
  if (type === 'presence') return value ? 'Oui' : 'Non'
  return Number(value).toFixed(1)
}

function selectSensor(sensor) {
  selectedSensor.value = sensor
  generateMockChartData()
}

// Stats computed from chart data
const stats = computed(() => {
  if (!chartData.value.length) return { min: '--', max: '--', avg: '--', count: 0 }
  
  const values = chartData.value.map(d => d.y)
  return {
    min: Math.min(...values).toFixed(1),
    max: Math.max(...values).toFixed(1),
    avg: (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1),
    count: values.length
  }
})

// Chart configuration
const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    toolbar: { show: false },
    background: 'transparent',
    animations: { enabled: true, easing: 'easeinout', speed: 800 }
  },
  colors: [getSensorColor(selectedSensor.value?.type)],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.1,
      stops: [0, 90, 100]
    }
  },
  stroke: { curve: 'smooth', width: 3 },
  grid: { borderColor: 'rgba(255, 255, 255, 0.1)', strokeDashArray: 4 },
  xaxis: {
    type: 'datetime',
    labels: { style: { colors: '#888' } }
  },
  yaxis: {
    labels: {
      style: { colors: '#888' },
      formatter: (val) => `${val.toFixed(1)} ${selectedSensor.value?.unit || ''}`
    }
  },
  tooltip: { theme: 'dark', x: { format: 'HH:mm:ss' } },
  dataLabels: { enabled: false }
}))

const chartSeries = computed(() => [{
  name: getSensorTypeName(selectedSensor.value?.type),
  data: chartData.value
}])

// Generate mock data for demo
function generateMockChartData() {
  if (!selectedSensor.value) return

  const now = Date.now()
  const data = []
  const points = chartPeriod.value === '1h' ? 60 : chartPeriod.value === '6h' ? 72 : chartPeriod.value === '24h' ? 96 : 168
  const interval = chartPeriod.value === '1h' ? 60000 : chartPeriod.value === '6h' ? 300000 : chartPeriod.value === '24h' ? 900000 : 3600000

  let baseValue = selectedSensor.value.type === 'temperature' ? 21 : 
                  selectedSensor.value.type === 'humidity' ? 45 :
                  selectedSensor.value.type === 'co2' ? 400 : 50

  for (let i = points; i >= 0; i--) {
    const variation = (Math.random() - 0.5) * (selectedSensor.value.type === 'co2' ? 100 : 5)
    baseValue += variation * 0.1
    data.push({
      x: now - i * interval,
      y: baseValue + variation
    })
  }

  chartData.value = data
}

function exportRoomData() {
  if (!room.value?.sensors?.length) return
  
  const data = room.value.sensors.map(s => ({
    salle: room.value.name,
    capteur: getSensorTypeName(s.type),
    valeur: s.value,
    unite: s.unit,
    statut: s.status
  }))
  
  exportToCSV(data, `salle_${room.value.id}`)
}

watch(chartPeriod, generateMockChartData)

onMounted(() => {
  if (room.value?.sensors?.length) {
    selectSensor(room.value.sensors[0])
  }
})
</script>

<style scoped lang="scss">
.room-view {
  max-width: 1400px;
  margin: 0 auto;
}

.room-hero {
  position: relative;
  border-radius: 24px;
  padding: 48px;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  color: white;
}

.room-info {
  color: white;
}

.hero-decoration {
  position: absolute;
  top: -50%;
  right: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.sensors-card, .info-card, .chart-card, .comparison-card {
  border-radius: 16px;
}

.sensors-list {
  .sensor-item {
    cursor: pointer;
    transition: background 0.2s ease;
    border-left: 3px solid transparent;

    &:hover {
      background: rgba(var(--v-theme-primary), 0.05);
    }

    &.active {
      background: rgba(var(--v-theme-primary), 0.1);
      border-left-color: rgb(var(--v-theme-primary));
    }
  }
}

.sensor-value {
  font-weight: 700;
  font-size: 1.1rem;
}

.sensor-unit {
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-left: 4px;
}

.stat-card {
  border-radius: 12px;
  
  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
  }
  
  .stat-label {
    font-size: 0.75rem;
    color: rgba(var(--v-theme-on-surface), 0.6);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.comparison-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  border-left: 4px solid;
}

.comparison-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.comparison-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.comparison-unit {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.comparison-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
