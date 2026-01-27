<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-6 flex-wrap ga-3">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Dashboard</h1>
        <p class="text-body-2 text-medium-emphasis">
          Bâtiment Orion - Campus CESI Nancy
        </p>
      </div>
      <div class="d-flex align-center ga-3">
        <v-chip color="primary" variant="tonal" size="large">
          <v-icon start class="pulse">mdi-circle</v-icon>
          Live
        </v-chip>
      </div>
    </div>

    <!-- Room Filter -->
    <v-card color="surface" class="mb-6">
      <v-card-text class="pa-4">
        <v-row align="center">
          <v-col cols="12" sm="4" md="3">
            <v-select
              v-model="selectedFloor"
              :items="floorOptions"
              item-title="name"
              item-value="id"
              label="Étage"
              variant="outlined"
              density="compact"
              hide-details
              prepend-inner-icon="mdi-stairs"
            />
          </v-col>
          <v-col cols="12" sm="5" md="4">
            <v-select
              v-model="selectedRoom"
              :items="roomOptions"
              item-title="label"
              item-value="id"
              label="Salle"
              variant="outlined"
              density="compact"
              hide-details
              prepend-inner-icon="mdi-door"
              clearable
              :disabled="!selectedFloor"
            />
          </v-col>
          <v-col cols="12" sm="3" md="2">
            <v-btn 
              color="primary" 
              variant="tonal" 
              block 
              @click="resetFilter"
              :disabled="!selectedRoom"
            >
              <v-icon start>mdi-refresh</v-icon>
              Tout voir
            </v-btn>
          </v-col>
          <v-col cols="12" md="3">
            <v-chip 
              v-if="selectedRoomData" 
              color="primary" 
              variant="flat"
              size="large"
              class="w-100 justify-center"
            >
              <v-icon start>mdi-map-marker</v-icon>
              {{ selectedRoomData.name }} ({{ selectedRoomData.id }})
            </v-chip>
            <v-chip 
              v-else 
              color="grey" 
              variant="tonal"
              size="large"
              class="w-100 justify-center"
            >
              <v-icon start>mdi-home</v-icon>
              Toutes les salles
            </v-chip>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Sensor Cards Grid -->
    <v-row>
      <!-- Temperature -->
      <v-col cols="12" sm="6" lg="4">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="error" variant="tonal" size="48">
                <v-icon size="24">mdi-thermometer</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(roomTemperature)]"></span>
            </div>
            <div class="sensor-value temperature mb-2">
              {{ formatValue(roomTemperature?.latest_value, 1) }}
              <span class="text-body-1 text-medium-emphasis">°C</span>
            </div>
            <div class="text-body-2 text-medium-emphasis">Température</div>
            <v-chip 
              v-if="roomTemperature?.location" 
              size="x-small" 
              color="error" 
              variant="tonal" 
              class="mt-2"
            >
              <v-icon start size="12">mdi-map-marker</v-icon>
              {{ roomTemperature.location }}
            </v-chip>
            <v-chip v-else size="x-small" color="grey" variant="outlined" class="mt-2">
              Non assigné
            </v-chip>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Humidity -->
      <v-col cols="12" sm="6" lg="4">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="info" variant="tonal" size="48">
                <v-icon size="24">mdi-water-percent</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(roomHumidity)]"></span>
            </div>
            <div class="sensor-value humidity mb-2">
              {{ formatValue(roomHumidity?.latest_value, 0) }}
              <span class="text-body-1 text-medium-emphasis">%</span>
            </div>
            <div class="text-body-2 text-medium-emphasis">Humidité</div>
            <v-chip 
              v-if="roomHumidity?.location" 
              size="x-small" 
              color="info" 
              variant="tonal" 
              class="mt-2"
            >
              <v-icon start size="12">mdi-map-marker</v-icon>
              {{ roomHumidity.location }}
            </v-chip>
            <v-chip v-else size="x-small" color="grey" variant="outlined" class="mt-2">
              Non assigné
            </v-chip>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Presence -->
      <v-col cols="12" sm="6" lg="4">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="success" variant="tonal" size="48">
                <v-icon size="24">mdi-motion-sensor</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(roomPresence)]"></span>
            </div>
            <div class="sensor-value presence mb-2">
              {{ roomPresence?.latest_value ? 'Oui' : 'Non' }}
            </div>
            <div class="text-body-2 text-medium-emphasis">Présence détectée</div>
            <v-chip 
              v-if="roomPresence?.location" 
              size="x-small" 
              color="success" 
              variant="tonal" 
              class="mt-2"
            >
              <v-icon start size="12">mdi-map-marker</v-icon>
              {{ roomPresence.location }}
            </v-chip>
            <v-chip v-else size="x-small" color="grey" variant="outlined" class="mt-2">
              Non assigné
            </v-chip>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts Row -->
    <v-row class="mt-4">
      <!-- Temperature Chart -->
      <v-col cols="12" lg="8">
        <v-card color="surface">
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-chart-line</v-icon>
            Évolution température
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="chartPeriod" mandatory density="compact" variant="outlined">
              <v-btn value="1h" size="small">1H</v-btn>
              <v-btn value="6h" size="small">6H</v-btn>
              <v-btn value="24h" size="small">24H</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text>
            <div class="chart-container">
              <apexchart
                v-if="chartData.length > 0"
                type="area"
                height="300"
                :options="chartOptions"
                :series="chartSeries"
              ></apexchart>
              <div v-else class="d-flex flex-column align-center justify-center" style="height: 300px">
                <v-icon size="48" color="grey" class="mb-2">mdi-chart-line-variant</v-icon>
                <p class="text-body-2 text-medium-emphasis">Aucune donnée disponible</p>
                <p class="text-caption text-medium-emphasis">Les données apparaîtront quand les capteurs enverront des mesures</p>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Alerts Summary -->
      <v-col cols="12" lg="4">
        <v-card color="surface" class="h-100">
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-bell-alert</v-icon>
            Alertes actives
            <v-spacer></v-spacer>
            <v-chip :color="alertCount > 0 ? 'error' : 'success'" size="small">
              {{ alertCount }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <v-list v-if="recentAlerts.length" bg-color="transparent" density="compact">
              <v-list-item
                v-for="alert in recentAlerts"
                :key="alert.id"
                :class="['alert-' + alert.severity, 'mb-2 rounded-lg']"
              >
                <template v-slot:prepend>
                  <v-icon :color="getSeverityColor(alert.severity)">
                    {{ getSeverityIcon(alert.severity) }}
                  </v-icon>
                </template>
                <v-list-item-title>{{ alert.message }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(alert.created_at) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-check-circle-outline</v-icon>
              <p>Aucune alerte active</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- System Status Row -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card color="surface">
          <v-card-title>
            <v-icon start>mdi-server</v-icon>
            État du système
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6" sm="3">
                <div class="text-center">
                  <div class="text-h4 font-weight-bold text-primary">
                    {{ sensors.length }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">Capteurs total</div>
                </div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="text-center">
                  <div class="text-h4 font-weight-bold text-success">
                    {{ onlineSensors.length }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">En ligne</div>
                </div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="text-center">
                  <div class="text-h4 font-weight-bold text-warning">
                    {{ alertCount }}
                  </div>
                  <div class="text-body-2 text-medium-emphasis">Alertes</div>
                </div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="text-center">
                  <div class="text-h4 font-weight-bold text-info">
                    {{ heatingValue }}%
                  </div>
                  <div class="text-body-2 text-medium-emphasis">Chauffage</div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'
import { useBuildingStore } from '@/stores/building'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

// Stores
const sensorsStore = useSensorsStore()
const alertsStore = useAlertsStore()
const buildingStore = useBuildingStore()

const { sensors, temperature, humidity, presence, onlineSensors } = storeToRefs(sensorsStore)
const { activeAlerts } = storeToRefs(alertsStore)
const { floors, rooms, sensors: buildingSensors } = storeToRefs(buildingStore)

// Room filter
const selectedFloor = ref('all')
const selectedRoom = ref(null)

// Floor options with "All" option
const floorOptions = computed(() => [
  { id: 'all', name: 'Tous les étages' },
  ...floors.value
])

// Room options based on selected floor
const roomOptions = computed(() => {
  if (!selectedFloor.value || selectedFloor.value === 'all') {
    return rooms.value
      .filter(r => r.type !== 'utility' && r.type !== 'common')
      .map(r => ({ id: r.id, label: `${r.name} (${r.id})` }))
  }
  return rooms.value
    .filter(r => r.floor === selectedFloor.value && r.type !== 'utility' && r.type !== 'common')
    .map(r => ({ id: r.id, label: `${r.name} (${r.id})` }))
})

// Selected room data
const selectedRoomData = computed(() => {
  if (!selectedRoom.value) return null
  return rooms.value.find(r => r.id === selectedRoom.value)
})

// Filtered sensors based on selected room
const filteredBuildingSensors = computed(() => {
  if (!selectedRoom.value) return buildingSensors.value
  return buildingSensors.value.filter(s => s.roomId === selectedRoom.value)
})

// Get aggregated sensor data (from API or building store)
const roomTemperature = computed(() => {
  // If a specific room is selected, get data from building sensors
  if (selectedRoom.value) {
    const sensor = filteredBuildingSensors.value.find(s => s.type === 'temperature')
    if (sensor) {
      return { 
        latest_value: sensor.value, 
        location: selectedRoomData.value?.name,
        status: sensor.status 
      }
    }
    return { latest_value: null, location: selectedRoomData.value?.name, status: 'offline' }
  }
  
  // No room selected - show global data from API or first available building sensor
  if (temperature.value?.latest_value !== undefined && temperature.value?.latest_value !== null) {
    return temperature.value
  }
  
  // Fallback to first temperature sensor in building
  const firstTempSensor = buildingSensors.value.find(s => s.type === 'temperature' && s.value !== null)
  if (firstTempSensor) {
    const room = rooms.value.find(r => r.id === firstTempSensor.roomId)
    return {
      latest_value: firstTempSensor.value,
      location: room?.name || firstTempSensor.roomId,
      status: firstTempSensor.status || 'ok'
    }
  }
  
  return { latest_value: null, location: null, status: 'offline' }
})

const roomHumidity = computed(() => {
  if (selectedRoom.value) {
    const sensor = filteredBuildingSensors.value.find(s => s.type === 'humidity')
    if (sensor) {
      return { 
        latest_value: sensor.value, 
        location: selectedRoomData.value?.name,
        status: sensor.status 
      }
    }
    return { latest_value: null, location: selectedRoomData.value?.name, status: 'offline' }
  }
  
  if (humidity.value?.latest_value !== undefined && humidity.value?.latest_value !== null) {
    return humidity.value
  }
  
  const firstHumSensor = buildingSensors.value.find(s => s.type === 'humidity' && s.value !== null)
  if (firstHumSensor) {
    const room = rooms.value.find(r => r.id === firstHumSensor.roomId)
    return {
      latest_value: firstHumSensor.value,
      location: room?.name || firstHumSensor.roomId,
      status: firstHumSensor.status || 'ok'
    }
  }
  
  return { latest_value: null, location: null, status: 'offline' }
})

const roomPresence = computed(() => {
  if (selectedRoom.value) {
    const sensor = filteredBuildingSensors.value.find(s => s.type === 'presence')
    if (sensor) {
      return { 
        latest_value: sensor.value, 
        location: selectedRoomData.value?.name,
        status: sensor.status 
      }
    }
    return { latest_value: null, location: selectedRoomData.value?.name, status: 'offline' }
  }
  
  if (presence.value?.latest_value !== undefined && presence.value?.latest_value !== null) {
    return presence.value
  }
  
  const firstPresSensor = buildingSensors.value.find(s => s.type === 'presence' && s.value !== null)
  if (firstPresSensor) {
    const room = rooms.value.find(r => r.id === firstPresSensor.roomId)
    return {
      latest_value: firstPresSensor.value,
      location: room?.name || firstPresSensor.roomId,
      status: firstPresSensor.status || 'ok'
    }
  }
  
  return { latest_value: null, location: null, status: 'offline' }
})

// Reset filter
function resetFilter() {
  selectedRoom.value = null
}

// Watch floor change to reset room
watch(selectedFloor, () => {
  selectedRoom.value = null
})

// Chart
const chartPeriod = ref('6h')
const chartData = ref([])
const heatingValue = ref(45) // Mock value

const alertCount = computed(() => activeAlerts.value.length)
const recentAlerts = computed(() => activeAlerts.value.slice(0, 5))

// Chart options
const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    toolbar: { show: false },
    background: 'transparent',
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800
    }
  },
  colors: ['#ff6b6b'],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.1,
      stops: [0, 90, 100]
    }
  },
  stroke: {
    curve: 'smooth',
    width: 3
  },
  grid: {
    borderColor: 'rgba(255, 255, 255, 0.1)',
    strokeDashArray: 4
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#888' }
    }
  },
  yaxis: {
    labels: {
      style: { colors: '#888' },
      formatter: (val) => `${val.toFixed(1)}°C`
    }
  },
  tooltip: {
    theme: 'dark',
    x: { format: 'HH:mm:ss' }
  },
  dataLabels: { enabled: false }
}))

const chartSeries = computed(() => [{
  name: 'Température',
  data: chartData.value
}])

// Helpers
function formatValue(value, decimals = 1) {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(decimals)
}

function getStatus(sensor) {
  if (!sensor?.status) return 'offline'
  return sensor.status
}

function getSeverityColor(severity) {
  const colors = {
    danger: 'error',
    warning: 'warning',
    info: 'info'
  }
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

// Generate mock data for demo (will be replaced by real data)
function generateMockChartData() {
  const now = Date.now()
  const data = []
  for (let i = 60; i >= 0; i--) {
    data.push({
      x: now - i * 60000, // 1 minute intervals
      y: 21 + Math.random() * 3 // Random temp between 21-24
    })
  }
  chartData.value = data
}

onMounted(() => {
  // Use mock data for now - will be replaced when real sensors send data
  generateMockChartData()
})
</script>
