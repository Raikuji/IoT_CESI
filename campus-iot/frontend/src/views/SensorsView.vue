<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Capteurs</h1>
        <p class="text-body-2 text-medium-emphasis">
          Gestion et monitoring des capteurs
        </p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-refresh" @click="refresh">
        Actualiser
      </v-btn>
    </div>

    <v-row>
      <v-col
        v-for="sensor in sensors"
        :key="sensor.id"
        cols="12"
        sm="6"
        lg="4"
      >
        <v-card class="glow-card" color="surface">
          <v-card-text class="pa-5">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="d-flex align-center">
                <v-avatar :color="getSensorColor(sensor.type)" variant="tonal" size="48" class="mr-3">
                  <v-icon size="24">{{ getSensorIcon(sensor.type) }}</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6">{{ sensor.name }}</div>
                  <div class="text-body-2 text-medium-emphasis">{{ sensor.location }}</div>
                </div>
              </div>
              <v-chip :color="getStatusColor(sensor.status)" size="small" variant="tonal">
                {{ sensor.status || 'offline' }}
              </v-chip>
            </div>

            <v-divider class="my-4"></v-divider>

            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-body-2 text-medium-emphasis mb-1">Dernière valeur</div>
                <div :class="['sensor-value', sensor.type]">
                  {{ formatValue(sensor.latest_value, sensor.type) }}
                  <span class="text-body-2 text-medium-emphasis">{{ sensor.unit }}</span>
                </div>
              </div>
              <div class="text-right">
                <div class="text-body-2 text-medium-emphasis mb-1">Mise à jour</div>
                <div class="text-body-1">{{ formatTime(sensor.latest_time) }}</div>
              </div>
            </div>

            <v-btn
              class="mt-4"
              variant="tonal"
              color="primary"
              block
              @click="showHistory(sensor)"
            >
              <v-icon start>mdi-chart-line</v-icon>
              Voir l'historique
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- History Dialog -->
    <v-dialog v-model="historyDialog" max-width="800">
      <v-card color="surface">
        <v-card-title class="d-flex align-center">
          <v-icon start>mdi-chart-line</v-icon>
          Historique - {{ selectedSensor?.name }}
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="historyDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="chart-container">
            <apexchart
              v-if="historyData.length"
              type="line"
              height="350"
              :options="historyChartOptions"
              :series="historySeries"
            ></apexchart>
            <div v-else class="d-flex align-center justify-center" style="height: 350px">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSensorsStore } from '@/stores/sensors'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const sensorsStore = useSensorsStore()
const { sensors } = storeToRefs(sensorsStore)

const historyDialog = ref(false)
const selectedSensor = ref(null)
const historyData = ref([])

function getSensorIcon(type) {
  const icons = {
    temperature: 'mdi-thermometer',
    humidity: 'mdi-water-percent',
    pressure: 'mdi-gauge',
    presence: 'mdi-motion-sensor',
    co2: 'mdi-molecule-co2'
  }
  return icons[type] || 'mdi-chip'
}

function getSensorColor(type) {
  const colors = {
    temperature: 'error',
    humidity: 'info',
    pressure: 'secondary',
    presence: 'success',
    co2: 'warning'
  }
  return colors[type] || 'grey'
}

function getStatusColor(status) {
  const colors = {
    ok: 'success',
    warning: 'warning',
    offline: 'error'
  }
  return colors[status] || 'grey'
}

function formatValue(value, type) {
  if (value === null || value === undefined) return '--'
  if (type === 'presence') return value ? 'Oui' : 'Non'
  return Number(value).toFixed(1)
}

function formatTime(time) {
  if (!time) return '--'
  return new Date(time).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function showHistory(sensor) {
  selectedSensor.value = sensor
  historyDialog.value = true
  historyData.value = []
  
  const data = await sensorsStore.fetchSensorData(sensor.id, { limit: 200 })
  historyData.value = data.map(d => ({
    x: new Date(d.time).getTime(),
    y: d.value
  })).reverse()
}

const historyChartOptions = computed(() => ({
  chart: {
    type: 'line',
    toolbar: { show: true },
    background: 'transparent'
  },
  colors: [getSensorColor(selectedSensor.value?.type) === 'error' ? '#ff6b6b' : '#00ff9d'],
  stroke: { curve: 'smooth', width: 2 },
  grid: { borderColor: 'rgba(255, 255, 255, 0.1)' },
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
  tooltip: { theme: 'dark' },
  dataLabels: { enabled: false }
}))

const historySeries = computed(() => [{
  name: selectedSensor.value?.name || 'Valeur',
  data: historyData.value
}])

function refresh() {
  sensorsStore.fetchSensors()
}
</script>
