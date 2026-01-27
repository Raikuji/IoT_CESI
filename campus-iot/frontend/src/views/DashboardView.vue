<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Dashboard</h1>
        <p class="text-body-2 text-medium-emphasis">
          Salle C101 - Campus CESI Cassiope
        </p>
      </div>
      <v-chip color="primary" variant="tonal" size="large">
        <v-icon start class="pulse">mdi-circle</v-icon>
        Live
      </v-chip>
    </div>

    <!-- Sensor Cards Grid -->
    <v-row>
      <!-- Temperature -->
      <v-col cols="12" sm="6" lg="3">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="error" variant="tonal" size="48">
                <v-icon size="24">mdi-thermometer</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(temperature)]"></span>
            </div>
            <div class="sensor-value temperature mb-2">
              {{ formatValue(temperature?.latest_value, 1) }}
              <span class="text-body-1 text-medium-emphasis">°C</span>
            </div>
            <div class="text-body-2 text-medium-emphasis">Température</div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Humidity -->
      <v-col cols="12" sm="6" lg="3">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="info" variant="tonal" size="48">
                <v-icon size="24">mdi-water-percent</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(humidity)]"></span>
            </div>
            <div class="sensor-value humidity mb-2">
              {{ formatValue(humidity?.latest_value, 0) }}
              <span class="text-body-1 text-medium-emphasis">%</span>
            </div>
            <div class="text-body-2 text-medium-emphasis">Humidité</div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Pressure -->
      <v-col cols="12" sm="6" lg="3">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="secondary" variant="tonal" size="48">
                <v-icon size="24">mdi-gauge</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(pressure)]"></span>
            </div>
            <div class="sensor-value pressure mb-2">
              {{ formatValue(pressure?.latest_value, 0) }}
              <span class="text-body-1 text-medium-emphasis">hPa</span>
            </div>
            <div class="text-body-2 text-medium-emphasis">Pression</div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Presence -->
      <v-col cols="12" sm="6" lg="3">
        <v-card class="glow-card h-100" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar color="success" variant="tonal" size="48">
                <v-icon size="24">mdi-motion-sensor</v-icon>
              </v-avatar>
              <span :class="['status-dot', getStatus(presence)]"></span>
            </div>
            <div class="sensor-value presence mb-2">
              {{ presence?.latest_value ? 'Oui' : 'Non' }}
            </div>
            <div class="text-body-2 text-medium-emphasis">Présence détectée</div>
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
              <v-btn value="1h" size="small">1h</v-btn>
              <v-btn value="6h" size="small">6h</v-btn>
              <v-btn value="24h" size="small">24h</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text>
            <div class="chart-container">
              <apexchart
                v-if="chartData.length"
                type="area"
                height="300"
                :options="chartOptions"
                :series="chartSeries"
              ></apexchart>
              <div v-else class="d-flex align-center justify-center" style="height: 300px">
                <v-progress-circular indeterminate color="primary"></v-progress-circular>
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
import { ref, computed, watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

// Stores
const sensorsStore = useSensorsStore()
const alertsStore = useAlertsStore()

const { sensors, temperature, humidity, pressure, presence, onlineSensors } = storeToRefs(sensorsStore)
const { activeAlerts } = storeToRefs(alertsStore)

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

// Fetch chart data
async function fetchChartData() {
  if (!temperature.value?.id) return
  
  const data = await sensorsStore.fetchSensorData(temperature.value.id, {
    limit: 100
  })
  
  chartData.value = data.map(d => ({
    x: new Date(d.time).getTime(),
    y: d.value
  })).reverse()
}

// Watch for period changes
watch(chartPeriod, fetchChartData)

onMounted(() => {
  fetchChartData()
})
</script>
