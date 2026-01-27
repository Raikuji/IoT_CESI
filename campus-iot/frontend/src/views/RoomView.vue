<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Plan Salle C101</h1>
        <p class="text-body-2 text-medium-emphasis">
          Vue interactive des capteurs
        </p>
      </div>
    </div>

    <v-row>
      <!-- Room Plan -->
      <v-col cols="12" lg="8">
        <v-card color="surface">
          <v-card-text class="pa-6">
            <div class="room-plan" :style="{ height: '500px', position: 'relative' }">
              <!-- Room outline -->
              <svg width="100%" height="100%" viewBox="0 0 400 300" class="room-svg">
                <!-- Room walls -->
                <rect x="10" y="10" width="380" height="280" fill="none" stroke="rgba(0, 255, 157, 0.3)" stroke-width="3" rx="8"/>
                
                <!-- Door -->
                <rect x="170" y="275" width="60" height="15" fill="rgba(0, 255, 157, 0.2)" stroke="rgba(0, 255, 157, 0.5)" stroke-width="2"/>
                <text x="200" y="287" text-anchor="middle" fill="rgba(255,255,255,0.5)" font-size="10">Porte</text>
                
                <!-- Windows -->
                <rect x="10" y="60" width="10" height="80" fill="rgba(0, 212, 255, 0.2)" stroke="rgba(0, 212, 255, 0.5)" stroke-width="2"/>
                <rect x="10" y="160" width="10" height="80" fill="rgba(0, 212, 255, 0.2)" stroke="rgba(0, 212, 255, 0.5)" stroke-width="2"/>
                
                <!-- Desks (simplified) -->
                <rect x="60" y="60" width="120" height="60" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" rx="4"/>
                <rect x="220" y="60" width="120" height="60" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" rx="4"/>
                <rect x="60" y="160" width="120" height="60" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" rx="4"/>
                <rect x="220" y="160" width="120" height="60" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" rx="4"/>
              </svg>

              <!-- Sensor markers -->
              <div
                v-for="marker in sensorMarkers"
                :key="marker.id"
                class="sensor-marker"
                :class="{ active: marker.status === 'ok' }"
                :style="{
                  left: marker.x + '%',
                  top: marker.y + '%',
                  background: marker.color,
                  transform: 'translate(-50%, -50%)'
                }"
                @click="selectSensor(marker)"
              >
                <v-icon color="white" size="20">{{ marker.icon }}</v-icon>
                <v-tooltip activator="parent" location="top">
                  {{ marker.name }}: {{ marker.value }} {{ marker.unit }}
                </v-tooltip>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Sensor Details -->
      <v-col cols="12" lg="4">
        <v-card color="surface" class="h-100">
          <v-card-title>
            <v-icon start>mdi-information</v-icon>
            Détails capteur
          </v-card-title>
          <v-card-text>
            <div v-if="selectedMarker" class="text-center">
              <v-avatar :color="selectedMarker.color" size="80" class="mb-4">
                <v-icon size="40" color="white">{{ selectedMarker.icon }}</v-icon>
              </v-avatar>
              
              <h3 class="text-h5 mb-2">{{ selectedMarker.name }}</h3>
              
              <div :class="['sensor-value', selectedMarker.type, 'mb-4']">
                {{ selectedMarker.value }}
                <span class="text-body-1 text-medium-emphasis">{{ selectedMarker.unit }}</span>
              </div>

              <v-chip :color="selectedMarker.status === 'ok' ? 'success' : 'warning'" class="mb-4">
                {{ selectedMarker.status === 'ok' ? 'En ligne' : 'Hors ligne' }}
              </v-chip>

              <v-list bg-color="transparent" density="compact">
                <v-list-item>
                  <v-list-item-title>Type</v-list-item-title>
                  <template v-slot:append>{{ selectedMarker.type }}</template>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Position</v-list-item-title>
                  <template v-slot:append>{{ selectedMarker.position }}</template>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Mise à jour</v-list-item-title>
                  <template v-slot:append>{{ formatTime(selectedMarker.time) }}</template>
                </v-list-item>
              </v-list>
            </div>
            
            <div v-else class="text-center py-12 text-medium-emphasis">
              <v-icon size="64" class="mb-4">mdi-cursor-default-click</v-icon>
              <p>Cliquez sur un capteur pour voir ses détails</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Legend -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card color="surface">
          <v-card-text>
            <div class="d-flex flex-wrap ga-4 justify-center">
              <v-chip
                v-for="legend in legendItems"
                :key="legend.type"
                :color="legend.color"
                variant="tonal"
              >
                <v-icon start>{{ legend.icon }}</v-icon>
                {{ legend.label }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSensorsStore } from '@/stores/sensors'

const sensorsStore = useSensorsStore()
const { sensors } = storeToRefs(sensorsStore)

const selectedMarker = ref(null)

const sensorMarkers = computed(() => {
  // Position sensors on the room plan
  const positions = {
    temperature: { x: 50, y: 20, position: 'Plafond centre' },
    humidity: { x: 50, y: 20, position: 'Plafond centre' },
    pressure: { x: 50, y: 20, position: 'Plafond centre' },
    presence: { x: 50, y: 90, position: 'Entrée (porte)' },
    co2: { x: 85, y: 50, position: 'Mur est' }
  }

  const colors = {
    temperature: '#ff6b6b',
    humidity: '#4ecdc4',
    pressure: '#a29bfe',
    presence: '#00ff9d',
    co2: '#ffa502'
  }

  const icons = {
    temperature: 'mdi-thermometer',
    humidity: 'mdi-water-percent',
    pressure: 'mdi-gauge',
    presence: 'mdi-motion-sensor',
    co2: 'mdi-molecule-co2'
  }

  return sensors.value.map(sensor => ({
    id: sensor.id,
    name: sensor.name,
    type: sensor.type,
    value: formatValue(sensor.latest_value, sensor.type),
    unit: sensor.unit,
    status: sensor.status || 'offline',
    time: sensor.latest_time,
    x: positions[sensor.type]?.x || 50,
    y: positions[sensor.type]?.y || 50,
    position: positions[sensor.type]?.position || 'Inconnu',
    color: colors[sensor.type] || '#888',
    icon: icons[sensor.type] || 'mdi-chip'
  }))
})

const legendItems = [
  { type: 'temperature', label: 'Température', color: 'error', icon: 'mdi-thermometer' },
  { type: 'humidity', label: 'Humidité', color: 'info', icon: 'mdi-water-percent' },
  { type: 'presence', label: 'Présence', color: 'success', icon: 'mdi-motion-sensor' },
  { type: 'co2', label: 'CO2', color: 'warning', icon: 'mdi-molecule-co2' }
]

function formatValue(value, type) {
  if (value === null || value === undefined) return '--'
  if (type === 'presence') return value ? 'Détecté' : 'Aucune'
  return Number(value).toFixed(1)
}

function formatTime(time) {
  if (!time) return '--'
  return new Date(time).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

function selectSensor(marker) {
  selectedMarker.value = marker
}
</script>

<style scoped>
.room-svg {
  position: absolute;
  top: 0;
  left: 0;
}

.sensor-marker {
  z-index: 10;
}
</style>
