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
                  <div class="text-body-2 text-medium-emphasis">
                    <v-chip 
                      v-if="sensor.location && sensor.location !== 'unknown'" 
                      size="x-small" 
                      color="success" 
                      variant="flat"
                    >
                      <v-icon start size="12">mdi-check-circle</v-icon>
                      {{ sensor.location }}
                    </v-chip>
                    <v-chip 
                      v-else 
                      size="x-small" 
                      color="warning" 
                      variant="tonal"
                    >
                      <v-icon start size="12">mdi-clock-outline</v-icon>
                      En attente de room
                    </v-chip>
                  </div>
                </div>
              </div>
              <v-chip :color="sensor.is_active ? 'success' : 'error'" size="small" variant="tonal">
                {{ sensor.is_active ? 'online' : 'offline' }}
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

            <div class="d-flex gap-2 mt-4">
              <v-btn
                variant="tonal"
                color="primary"
                size="small"
                @click="showHistory(sensor)"
              >
                <v-icon start>mdi-chart-line</v-icon>
                Historique
              </v-btn>
              <v-btn
                variant="tonal"
                color="info"
                size="small"
                :to="`/building?room=${sensor.location}`"
                :disabled="!sensor.location || sensor.location === 'unknown'"
              >
                <v-icon start>mdi-cube-outline</v-icon>
                Voir en 3D
              </v-btn>
              <v-btn
                variant="tonal"
                color="error"
                size="small"
                @click="openDeleteDialog(sensor)"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty state -->
    <v-card v-if="sensors.length === 0" class="text-center pa-8" color="surface">
      <v-icon size="64" color="grey">mdi-chip</v-icon>
      <h3 class="mt-4 text-h6">Aucun capteur détecté</h3>
      <p class="text-body-2 text-medium-emphasis mt-2">
        Les capteurs apparaîtront ici automatiquement quand ils enverront des données via MQTT
      </p>
      <v-alert type="info" variant="tonal" class="mt-4 text-left" density="compact">
        <div class="text-body-2">
          <strong>Format attendu :</strong><br>
          Topic: <code>campus/orion/sensors/{TYPE}</code><br>
          Payload: <code>{"room": "X101", "value": 23.5}</code>
        </div>
      </v-alert>
    </v-card>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card color="surface">
        <v-card-title class="d-flex align-center">
          <v-icon start color="error">mdi-delete-alert</v-icon>
          Supprimer le capteur
        </v-card-title>
        <v-card-text>
          <p>Êtes-vous sûr de vouloir supprimer le capteur <strong>{{ sensorToDelete?.name }}</strong> ?</p>
          <v-alert type="warning" variant="tonal" class="mt-4" density="compact">
            Cette action est irréversible. Toutes les données historiques seront perdues.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">Annuler</v-btn>
          <v-btn 
            color="error" 
            variant="elevated"
            :loading="deleting"
            @click="deleteSensor"
          >
            <v-icon start>mdi-delete</v-icon>
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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
import { useBuildingStore } from '@/stores/building'
import VueApexCharts from 'vue3-apexcharts'
import axios from 'axios'

const apexchart = VueApexCharts

const sensorsStore = useSensorsStore()
const buildingStore = useBuildingStore()
const { sensors } = storeToRefs(sensorsStore)

const historyDialog = ref(false)
const deleteDialog = ref(false)
const selectedSensor = ref(null)
const sensorToDelete = ref(null)
const historyData = ref([])
const deleting = ref(false)

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

// Open delete confirmation dialog
function openDeleteDialog(sensor) {
  sensorToDelete.value = sensor
  deleteDialog.value = true
}

// Delete sensor
async function deleteSensor() {
  if (!sensorToDelete.value) return
  
  deleting.value = true
  try {
    await axios.delete(`/api/sensors/${sensorToDelete.value.id}`)
    
    // Also remove from placed_sensors if exists
    const placedSensor = buildingStore.sensors.find(
      s => s.type === sensorToDelete.value.type && s.room_id === sensorToDelete.value.location
    )
    if (placedSensor) {
      await buildingStore.removeSensor(placedSensor.id)
    }
    
    // Refresh sensors list
    await sensorsStore.fetchSensors()
    
    deleteDialog.value = false
    sensorToDelete.value = null
  } catch (e) {
    console.error('Failed to delete sensor:', e)
  } finally {
    deleting.value = false
  }
}

function refresh() {
  sensorsStore.fetchSensors()
}
</script>
