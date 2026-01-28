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
                      variant="tonal"
                    >
                      <v-icon start size="12">mdi-map-marker</v-icon>
                      {{ getRoomName(sensor.location) }}
                    </v-chip>
                    <v-chip 
                      v-else 
                      size="x-small" 
                      color="warning" 
                      variant="tonal"
                    >
                      <v-icon start size="12">mdi-alert</v-icon>
                      Non assigné
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
                color="secondary"
                class="flex-grow-1"
                @click="openAssignDialog(sensor)"
              >
                <v-icon start>mdi-map-marker-plus</v-icon>
                Assigner
              </v-btn>
              <v-btn
                variant="tonal"
                color="primary"
                class="flex-grow-1"
                @click="showHistory(sensor)"
              >
                <v-icon start>mdi-chart-line</v-icon>
                Historique
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
      <v-chip class="mt-4" color="info" variant="tonal">
        Topic: campus/orion/sensors/{TYPE}
      </v-chip>
    </v-card>

    <!-- Assign Room Dialog -->
    <v-dialog v-model="assignDialog" max-width="500">
      <v-card color="surface">
        <v-card-title class="d-flex align-center">
          <v-icon start color="secondary">mdi-map-marker-plus</v-icon>
          Assigner à une salle
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="assignDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="text-body-1 mb-4">
            Capteur: <strong>{{ selectedSensor?.name }}</strong>
          </div>
          
          <!-- Floor Selection -->
          <v-select
            v-model="selectedFloor"
            :items="floors"
            item-title="name"
            item-value="id"
            label="Étage"
            variant="outlined"
            class="mb-4"
            prepend-inner-icon="mdi-stairs"
          ></v-select>
          
          <!-- Room Selection -->
          <v-select
            v-model="selectedRoom"
            :items="filteredRooms"
            item-title="displayName"
            item-value="id"
            label="Salle"
            variant="outlined"
            prepend-inner-icon="mdi-door"
            :disabled="!selectedFloor"
          ></v-select>
          
          <v-alert 
            v-if="selectedRoom" 
            type="info" 
            variant="tonal" 
            class="mt-4"
            density="compact"
          >
            <div class="d-flex align-center">
              <v-icon start>mdi-information</v-icon>
              <span>Le capteur sera visible sur le plan 3D dans la salle <strong>{{ selectedRoom }}</strong></span>
            </div>
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="assignDialog = false">Annuler</v-btn>
          <v-btn 
            color="secondary" 
            variant="elevated"
            :disabled="!selectedRoom"
            :loading="assigning"
            @click="assignSensorToRoom"
          >
            <v-icon start>mdi-check</v-icon>
            Assigner
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
const { floors, rooms } = storeToRefs(buildingStore)

const historyDialog = ref(false)
const assignDialog = ref(false)
const selectedSensor = ref(null)
const historyData = ref([])
const selectedFloor = ref(null)
const selectedRoom = ref(null)
const assigning = ref(false)

// Get rooms filtered by floor
const filteredRooms = computed(() => {
  if (!selectedFloor.value) return []
  return rooms.value
    .filter(r => r.floor === selectedFloor.value && r.type !== 'utility')
    .map(r => ({
      ...r,
      displayName: `${r.id} - ${r.name}`
    }))
})

// Get room name from ID
function getRoomName(location) {
  const room = rooms.value.find(r => r.id === location)
  return room ? `${room.id} - ${room.name}` : location
}

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

// Open assign dialog
function openAssignDialog(sensor) {
  selectedSensor.value = sensor
  selectedFloor.value = null
  selectedRoom.value = null
  assignDialog.value = true
}

// Assign sensor to room
async function assignSensorToRoom() {
  if (!selectedSensor.value || !selectedRoom.value) return
  
  assigning.value = true
  try {
    // Update sensor location in backend
    await axios.put(`/api/sensors/${selectedSensor.value.id}`, {
      location: selectedRoom.value
    })
    
    // Also add to placed_sensors for 3D visualization
    await buildingStore.addSensor({
      type: selectedSensor.value.type,
      roomId: selectedRoom.value,
      name: selectedSensor.value.name,
      x: 0.5,
      y: 0.5
    })
    
    // Refresh sensors list
    await sensorsStore.fetchSensors()
    
    assignDialog.value = false
  } catch (e) {
    console.error('Failed to assign sensor:', e)
  } finally {
    assigning.value = false
  }
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
