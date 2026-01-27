<template>
  <div class="building-view">
    <!-- Header with floor selector -->
    <v-card class="mb-6 header-card">
      <v-card-text class="d-flex align-center justify-space-between flex-wrap ga-4">
        <div class="d-flex align-center ga-4">
          <div class="building-icon">
            <v-icon size="32" color="primary">mdi-office-building</v-icon>
          </div>
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Bâtiment Orion</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              CESI Nancy • {{ currentFloorRooms.length }} salles • {{ currentFloorSensors.length }} capteurs actifs
            </p>
          </div>
        </div>
        
        <!-- Floor selector -->
        <v-btn-toggle
          v-model="selectedFloor"
          mandatory
          rounded="lg"
          color="primary"
          class="floor-toggle"
        >
          <v-btn
            v-for="floor in floors"
            :key="floor.id"
            :value="floor.id"
            variant="outlined"
            class="px-6"
          >
            <v-icon start>mdi-layers</v-icon>
            {{ floor.id }}
          </v-btn>
        </v-btn-toggle>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- Building Plan -->
      <v-col cols="12" lg="9">
        <v-card class="plan-card">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>
              <v-icon start color="primary">mdi-floor-plan</v-icon>
              Plan {{ selectedFloor }}
            </span>
            <div class="d-flex ga-2">
              <v-btn
                icon
                variant="text"
                size="small"
                @click="zoomIn"
              >
                <v-icon>mdi-magnify-plus</v-icon>
              </v-btn>
              <v-btn
                icon
                variant="text"
                size="small"
                @click="zoomOut"
              >
                <v-icon>mdi-magnify-minus</v-icon>
              </v-btn>
              <v-btn
                icon
                variant="text"
                size="small"
                @click="resetZoom"
              >
                <v-icon>mdi-fit-to-screen</v-icon>
              </v-btn>
            </div>
          </v-card-title>
          
            <v-card-text class="pa-0">
            <!-- Scrollable container -->
            <div 
              class="plan-scroll-wrapper"
              ref="planContainer"
              @mousedown="startPan"
              @mousemove="doPan"
              @mouseup="endPan"
              @mouseleave="endPan"
            >
              <svg
                :viewBox="`0 0 200 100`"
                class="building-svg"
                preserveAspectRatio="xMidYMid meet"
                :style="{ transform: `scale(${zoom}) translate(${panX}px, ${panY}px)` }"
              >
                <!-- Background grid -->
                <defs>
                  <pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse">
                    <path d="M 5 0 L 0 0 0 5" fill="none" stroke="currentColor" stroke-width="0.1" opacity="0.1"/>
                  </pattern>
                  
                  <!-- Glow filter for selected room -->
                  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="0.8" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                <!-- Background -->
                <rect width="200" height="100" fill="url(#grid)" class="plan-bg"/>
                
                <!-- Building outline - Long rectangular shape like real Orion -->
                <rect 
                  x="2" y="5" 
                  width="196" height="90" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="0.4"
                  opacity="0.4"
                  rx="0.5"
                />
                
                <!-- Floor indicator -->
                <text x="50" y="3" text-anchor="middle" font-size="2" fill="currentColor" opacity="0.5">
                  {{ selectedFloor }} - Bâtiment Orion
                </text>
                
                <!-- Compass -->
                <g transform="translate(5, 72)">
                  <circle cx="0" cy="0" r="3" fill="none" stroke="currentColor" stroke-width="0.2" opacity="0.3"/>
                  <text x="0" y="-1" text-anchor="middle" font-size="2" fill="currentColor" opacity="0.5">N</text>
                  <line x1="0" y1="0" x2="0" y2="-2" stroke="currentColor" stroke-width="0.3" opacity="0.5"/>
                </g>
                
                <!-- Rooms -->
                <g v-for="room in currentFloorRooms" :key="room.id">
                  <!-- Clip path for this room -->
                  <defs>
                    <clipPath :id="`clip-${room.id}`">
                      <rect :x="room.x + 1" :y="room.y + 1" :width="room.width - 2" :height="room.height - 2" />
                    </clipPath>
                  </defs>
                  
                  <rect
                    :x="room.x"
                    :y="room.y"
                    :width="room.width"
                    :height="room.height"
                    :class="[
                      'room',
                      `room-${room.type}`,
                      { 'room-selected': selectedRoom?.id === room.id },
                      { 'room-has-sensors': getRoomSensors(room.id).length > 0 }
                    ]"
                    :filter="selectedRoom?.id === room.id ? 'url(#glow)' : ''"
                    rx="1"
                    @click="selectRoom(room)"
                    @dragover.prevent
                    @drop="handleDrop($event, room)"
                  />
                  
                  <!-- Text group clipped to room bounds -->
                  <g :clip-path="`url(#clip-${room.id})`">
                    <!-- Room ID -->
                    <text
                      :x="room.x + room.width / 2"
                      :y="room.y + room.height / 2 - (room.height > 18 ? 3 : 0)"
                      class="room-label"
                      :font-size="getRoomFontSize(room)"
                      text-anchor="middle"
                      dominant-baseline="middle"
                      @click="selectRoom(room)"
                    >
                      {{ room.id }}
                    </text>
                    
                    <!-- Room name (only if room is big enough) -->
                    <text
                      v-if="room.width >= 16 && room.height >= 18"
                      :x="room.x + room.width / 2"
                      :y="room.y + room.height / 2 + 4"
                      class="room-name"
                      :font-size="Math.max(2, Math.min(room.width / 8, 3))"
                      text-anchor="middle"
                      dominant-baseline="middle"
                    >
                      {{ room.name }}
                    </text>
                  </g>
                  
                  <!-- Sensor indicators -->
                  <g v-if="getRoomSensors(room.id).length > 0">
                    <circle
                      v-for="(sensor, idx) in getRoomSensors(room.id).slice(0, 3)"
                      :key="sensor.id"
                      :cx="room.x + 1.5 + idx * 2.5"
                      :cy="room.y + 1.5"
                      r="1"
                      :fill="getSensorColor(sensor.type)"
                      class="sensor-dot"
                      :class="{ 'sensor-dot-active': sensor.status === 'ok' }"
                    />
                    <text
                      v-if="getRoomSensors(room.id).length > 3"
                      :x="room.x + 10"
                      :y="room.y + 2"
                      font-size="1.5"
                      fill="currentColor"
                      opacity="0.7"
                    >
                      +{{ getRoomSensors(room.id).length - 3 }}
                    </text>
                  </g>
                </g>
                
                <!-- Stairs/Elevator symbol -->
                <g v-if="selectedFloor === 'R+1'" transform="translate(17, 56)">
                  <rect x="0" y="0" width="3" height="8" fill="none" stroke="currentColor" stroke-width="0.2" opacity="0.3"/>
                  <line x1="0.5" y1="2" x2="2.5" y2="2" stroke="currentColor" stroke-width="0.15" opacity="0.3"/>
                  <line x1="0.5" y1="4" x2="2.5" y2="4" stroke="currentColor" stroke-width="0.15" opacity="0.3"/>
                  <line x1="0.5" y1="6" x2="2.5" y2="6" stroke="currentColor" stroke-width="0.15" opacity="0.3"/>
                </g>
              </svg>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Sidebar -->
      <v-col cols="12" lg="3">
        <!-- Sensor Palette -->
        <v-card class="mb-4 sensor-palette">
          <v-card-title>
            <v-icon start color="primary">mdi-chip</v-icon>
            Ajouter un capteur
          </v-card-title>
          <v-card-subtitle>Glissez-déposez sur une salle</v-card-subtitle>
          <v-card-text>
            <div class="sensor-grid">
              <div
                v-for="sensorType in sensorTypes"
                :key="sensorType.type"
                class="sensor-item"
                draggable="true"
                @dragstart="startDrag($event, sensorType)"
              >
                <v-icon :color="sensorType.color" size="24">{{ sensorType.icon }}</v-icon>
                <span class="sensor-name">{{ sensorType.name }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Selected Room Info -->
        <v-card v-if="selectedRoom" class="room-info-card">
          <v-card-title class="d-flex align-center">
            <v-icon start :color="getRoomTypeColor(selectedRoom.type)">
              {{ getRoomTypeIcon(selectedRoom.type) }}
            </v-icon>
            {{ selectedRoom.name }}
            <v-spacer />
            <v-btn icon variant="text" size="small" @click="selectedRoom = null">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-chip
              size="small"
              :color="getRoomTypeColor(selectedRoom.type)"
              variant="tonal"
              class="mb-3"
            >
              {{ getRoomTypeLabel(selectedRoom.type) }}
            </v-chip>
            
            <div class="room-stats mb-4">
              <div class="stat">
                <v-icon size="16" class="mr-1">mdi-account-group</v-icon>
                <span>{{ selectedRoom.capacity }} places</span>
              </div>
              <div class="stat">
                <v-icon size="16" class="mr-1">mdi-chip</v-icon>
                <span>{{ getRoomSensors(selectedRoom.id).length }} capteurs</span>
              </div>
            </div>

            <!-- Room Sensors -->
            <div v-if="getRoomSensors(selectedRoom.id).length > 0" class="room-sensors">
              <h4 class="text-subtitle-2 mb-2">Capteurs installés</h4>
              <v-list density="compact" class="bg-transparent">
                <v-list-item
                  v-for="sensor in getRoomSensors(selectedRoom.id)"
                  :key="sensor.id"
                  class="sensor-list-item px-0"
                >
                  <template v-slot:prepend>
                    <v-avatar :color="getSensorColor(sensor.type)" size="32" class="mr-3">
                      <v-icon size="18" color="white">{{ getSensorIcon(sensor.type) }}</v-icon>
                    </v-avatar>
                  </template>
                  <v-list-item-title>{{ getSensorTypeName(sensor.type) }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <span v-if="sensor.value !== null" class="sensor-value">
                      {{ formatSensorValue(sensor) }}
                    </span>
                    <span v-else class="text-medium-emphasis">En attente...</span>
                  </v-list-item-subtitle>
                  <template v-slot:append>
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      color="error"
                      @click="removeSensor(sensor.id)"
                    >
                      <v-icon size="16">mdi-delete</v-icon>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            
            <div v-else class="text-center py-4">
              <v-icon size="48" color="grey" class="mb-2">mdi-chip-off</v-icon>
              <p class="text-body-2 text-medium-emphasis">Aucun capteur installé</p>
              <p class="text-caption text-medium-emphasis">Glissez un capteur sur cette salle</p>
            </div>
          </v-card-text>
        </v-card>

        <!-- Legend -->
        <v-card class="legend-card">
          <v-card-title>
            <v-icon start color="primary">mdi-map-legend</v-icon>
            Légende
          </v-card-title>
          <v-card-text>
            <div class="legend-grid">
              <div class="legend-item">
                <div class="legend-color room-classroom"></div>
                <span>Salle de cours</span>
              </div>
              <div class="legend-item">
                <div class="legend-color room-lab"></div>
                <span>Laboratoire</span>
              </div>
              <div class="legend-item">
                <div class="legend-color room-meeting"></div>
                <span>Réunion</span>
              </div>
              <div class="legend-item">
                <div class="legend-color room-office"></div>
                <span>Bureau</span>
              </div>
              <div class="legend-item">
                <div class="legend-color room-common"></div>
                <span>Espace commun</span>
              </div>
              <div class="legend-item">
                <div class="legend-color room-utility"></div>
                <span>Local technique</span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Fermer</v-btn>
      </template>
    </v-snackbar>

    <!-- Dialog for sensor positioning -->
    <v-dialog v-model="positionDialog.show" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-avatar :color="positionDialog.sensorType?.color" size="36" class="mr-3">
            <v-icon color="white">{{ positionDialog.sensorType?.icon }}</v-icon>
          </v-avatar>
          Positionner le capteur
        </v-card-title>
        <v-card-subtitle>
          {{ positionDialog.sensorType?.name }} dans {{ positionDialog.room?.name }}
        </v-card-subtitle>
        <v-card-text>
          <!-- Mini room preview for positioning -->
          <div class="position-preview mb-4">
            <div 
              class="preview-room"
              @click="setPositionFromClick"
              ref="previewRoom"
            >
              <div class="preview-grid"></div>
              <!-- Position marker -->
              <div 
                class="position-marker"
                :style="{
                  left: positionDialog.x + '%',
                  top: positionDialog.y + '%',
                  background: positionDialog.sensorType?.color
                }"
              >
                <v-icon color="white" size="16">{{ positionDialog.sensorType?.icon }}</v-icon>
              </div>
              <!-- Room labels -->
              <div class="preview-label top">Fond de salle</div>
              <div class="preview-label bottom">Entrée</div>
              <div class="preview-label left">Fenêtres</div>
              <div class="preview-label right">Couloir</div>
            </div>
          </div>

          <p class="text-body-2 text-medium-emphasis mb-4 text-center">
            Cliquez sur la zone pour positionner le capteur
          </p>

          <!-- Position sliders -->
          <v-row>
            <v-col cols="6">
              <v-slider
                v-model="positionDialog.x"
                :min="5"
                :max="95"
                :step="1"
                label="Position X"
                thumb-label
                color="primary"
              ></v-slider>
            </v-col>
            <v-col cols="6">
              <v-slider
                v-model="positionDialog.y"
                :min="5"
                :max="95"
                :step="1"
                label="Position Y"
                thumb-label
                color="primary"
              ></v-slider>
            </v-col>
          </v-row>

          <!-- Quick position buttons -->
          <div class="quick-positions mb-4">
            <v-chip 
              v-for="pos in quickPositions" 
              :key="pos.name"
              size="small"
              variant="outlined"
              class="mr-2 mb-2"
              @click="setQuickPosition(pos)"
            >
              {{ pos.name }}
            </v-chip>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="positionDialog.show = false">Annuler</v-btn>
          <v-btn color="primary" variant="flat" @click="confirmSensorPosition">
            <v-icon start>mdi-check</v-icon>
            Confirmer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useBuildingStore } from '@/stores/building'
import { storeToRefs } from 'pinia'

const buildingStore = useBuildingStore()
const { 
  currentFloor, 
  floors, 
  currentFloorRooms, 
  currentFloorSensors,
  sensorTypes 
} = storeToRefs(buildingStore)

// Local state
const selectedFloor = ref(currentFloor.value)
const selectedRoom = ref(null)
// Default zoom to see the whole plan (1 = 100%)
const DEFAULT_ZOOM = 1
const DEFAULT_PAN_X = 0
const DEFAULT_PAN_Y = 0
const zoom = ref(DEFAULT_ZOOM)
const panX = ref(DEFAULT_PAN_X)
const panY = ref(DEFAULT_PAN_Y)
const isPanning = ref(false)
const lastPanPoint = ref({ x: 0, y: 0 })
const draggedSensor = ref(null)
const snackbar = ref({ show: false, text: '', color: 'success' })
const previewRoom = ref(null)

// Position dialog
const positionDialog = ref({
  show: false,
  room: null,
  sensorType: null,
  x: 50,
  y: 50
})

// Quick position presets
const quickPositions = [
  { name: 'Centre', x: 50, y: 50 },
  { name: 'Entrée', x: 50, y: 90 },
  { name: 'Fond', x: 50, y: 10 },
  { name: 'Fenêtre', x: 10, y: 50 },
  { name: 'Couloir', x: 90, y: 50 },
  { name: 'Plafond centre', x: 50, y: 30 }
]

// Watch floor changes
watch(selectedFloor, (newFloor) => {
  buildingStore.setFloor(newFloor)
  selectedRoom.value = null
})

// Methods
function selectRoom(room) {
  selectedRoom.value = room
}

function getRoomSensors(roomId) {
  return buildingStore.getRoomSensors(roomId)
}

function getSensorColor(type) {
  const colors = {
    temperature: '#ff6b6b',
    humidity: '#4ecdc4',
    pressure: '#a855f7',
    presence: '#fbbf24',
    co2: '#22c55e',
    light: '#f59e0b'
  }
  return colors[type] || '#888'
}

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

function getSensorTypeName(type) {
  const names = {
    temperature: 'Température',
    humidity: 'Humidité',
    pressure: 'Pression',
    presence: 'Présence',
    co2: 'CO2',
    light: 'Luminosité'
  }
  return names[type] || type
}

function formatSensorValue(sensor) {
  if (sensor.value === null) return '—'
  
  switch (sensor.type) {
    case 'temperature':
      return `${sensor.value.toFixed(1)}°C`
    case 'humidity':
      return `${sensor.value.toFixed(0)}%`
    case 'pressure':
      return `${sensor.value.toFixed(0)} hPa`
    case 'presence':
      return sensor.value ? 'Détecté' : 'Vide'
    case 'co2':
      return `${sensor.value} ppm`
    case 'light':
      return `${sensor.value} lux`
    default:
      return sensor.value
  }
}

function getRoomTypeLabel(type) {
  const labels = {
    classroom: 'Cours',
    lab: 'Labo',
    meeting: 'Réunion',
    office: 'Bureau',
    common: 'Commun',
    utility: 'Tech.'
  }
  return labels[type] || type
}

function getRoomTypeIcon(type) {
  const icons = {
    classroom: 'mdi-school',
    lab: 'mdi-flask',
    meeting: 'mdi-account-group',
    office: 'mdi-desk',
    common: 'mdi-sofa',
    utility: 'mdi-wrench'
  }
  return icons[type] || 'mdi-door'
}

function getRoomTypeColor(type) {
  const colors = {
    classroom: 'blue',
    lab: 'purple',
    meeting: 'orange',
    office: 'green',
    common: 'teal',
    utility: 'grey'
  }
  return colors[type] || 'grey'
}

// Calculate font size based on room dimensions
function getRoomFontSize(room) {
  // Font size proportional to the smallest dimension
  const minDim = Math.min(room.width, room.height)
  // Scale: small rooms get smaller text, big rooms get bigger text
  // Clamp between 2.5 and 5
  return Math.max(2.5, Math.min(minDim / 4, 5))
}

// Zoom & Pan
function zoomIn() {
  zoom.value = Math.min(zoom.value + 0.25, 3)
}

function zoomOut() {
  zoom.value = Math.max(zoom.value - 0.25, 0.5)
}

function resetZoom() {
  zoom.value = DEFAULT_ZOOM
  panX.value = DEFAULT_PAN_X
  panY.value = DEFAULT_PAN_Y
}

// Disabled wheel zoom - only pan with mouse
function handleWheel(e) {
  // Do nothing - zoom disabled
}

function startPan(e) {
  if (e.button === 0) {
    isPanning.value = true
    lastPanPoint.value = { x: e.clientX, y: e.clientY }
  }
}

function doPan(e) {
  if (isPanning.value) {
    const dx = e.clientX - lastPanPoint.value.x
    const dy = e.clientY - lastPanPoint.value.y
    panX.value += dx
    panY.value += dy
    lastPanPoint.value = { x: e.clientX, y: e.clientY }
  }
}

function endPan() {
  isPanning.value = false
}

// Drag & Drop
function startDrag(e, sensorType) {
  draggedSensor.value = sensorType
  e.dataTransfer.effectAllowed = 'copy'
  e.dataTransfer.setData('text/plain', sensorType.type)
}

function handleDrop(e, room) {
  if (draggedSensor.value) {
    // Open position dialog instead of adding directly
    positionDialog.value = {
      show: true,
      room: room,
      sensorType: draggedSensor.value,
      x: 50,
      y: 50
    }
    selectedRoom.value = room
  }
}

function setPositionFromClick(e) {
  if (previewRoom.value) {
    const rect = previewRoom.value.getBoundingClientRect()
    const x = Math.round(((e.clientX - rect.left) / rect.width) * 100)
    const y = Math.round(((e.clientY - rect.top) / rect.height) * 100)
    positionDialog.value.x = Math.max(5, Math.min(95, x))
    positionDialog.value.y = Math.max(5, Math.min(95, y))
  }
}

function setQuickPosition(pos) {
  positionDialog.value.x = pos.x
  positionDialog.value.y = pos.y
}

function confirmSensorPosition() {
  const { room, sensorType, x, y } = positionDialog.value
  
  buildingStore.addSensor({
    type: sensorType.type,
    roomId: room.id,
    name: `${getSensorTypeName(sensorType.type)} ${room.id}`,
    x: x,
    y: y,
    unit: getUnitForType(sensorType.type)
  })
  
  snackbar.value = {
    show: true,
    text: `Capteur ${getSensorTypeName(sensorType.type)} ajouté à ${room.name}`,
    color: 'success'
  }
  
  positionDialog.value.show = false
  draggedSensor.value = null
}

function getUnitForType(type) {
  const units = {
    temperature: '°C',
    humidity: '%',
    pressure: 'hPa',
    presence: '',
    co2: 'ppm',
    light: 'lux'
  }
  return units[type] || ''
}

function removeSensor(sensorId) {
  buildingStore.removeSensor(sensorId)
  snackbar.value = {
    show: true,
    text: 'Capteur supprimé',
    color: 'warning'
  }
}
</script>

<style scoped lang="scss">
.building-view {
  min-height: 100%;
}

.header-card {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, transparent 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.building-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(var(--v-theme-primary), 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.floor-toggle {
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.plan-card {
  height: calc(100vh - 280px);
  min-height: 500px;
  display: flex;
  flex-direction: column;
}

.plan-scroll-wrapper {
  flex: 1;
  min-height: 500px;
  overflow: hidden;
  border-radius: 0 0 8px 8px;
  position: relative;
  cursor: grab;
  user-select: none;
  background: 
    radial-gradient(circle at 50% 50%, rgba(var(--v-theme-primary), 0.03) 0%, transparent 70%),
    linear-gradient(rgba(var(--v-theme-surface-variant), 0.3) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--v-theme-surface-variant), 0.3) 1px, transparent 1px);
  background-size: 100% 100%, 20px 20px, 20px 20px;
  
  &:active {
    cursor: grabbing;
  }
}


.building-svg {
  width: 100%;
  height: 100%;
  transform-origin: center center;
  color: rgb(var(--v-theme-on-surface));
}

.plan-bg {
  fill: transparent;
}

.room {
  fill: rgba(var(--v-theme-surface-variant), 0.5);
  stroke: rgba(var(--v-theme-on-surface), 0.3);
  stroke-width: 0.3;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    fill: rgba(var(--v-theme-primary), 0.2);
    stroke: rgb(var(--v-theme-primary));
    stroke-width: 0.5;
  }
  
  &.room-selected {
    fill: rgba(var(--v-theme-primary), 0.3);
    stroke: rgb(var(--v-theme-primary));
    stroke-width: 0.8;
  }
  
  &.room-has-sensors {
    fill: rgba(var(--v-theme-success), 0.15);
  }
  
  // Room type colors
  &.room-classroom { fill: rgba(66, 133, 244, 0.15); }
  &.room-lab { fill: rgba(156, 39, 176, 0.15); }
  &.room-meeting { fill: rgba(255, 152, 0, 0.15); }
  &.room-office { fill: rgba(76, 175, 80, 0.15); }
  &.room-common { fill: rgba(0, 188, 212, 0.15); }
  &.room-utility { fill: rgba(158, 158, 158, 0.15); }
}

.room-label {
  font-weight: 700;
  fill: currentColor;
  pointer-events: none;
  user-select: none;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.room-name {
  fill: currentColor;
  opacity: 0.7;
  pointer-events: none;
  user-select: none;
}

.room-area {
  font-size: 2px;
  fill: currentColor;
  opacity: 0.4;
  pointer-events: none;
  user-select: none;
}

.sensor-dot {
  opacity: 0.8;
  
  &.sensor-dot-active {
    animation: pulse 2s infinite;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 0.4; }
}

// Sensor Palette
.sensor-palette {
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.sensor-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  cursor: grab;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  
  &:hover {
    background: rgba(var(--v-theme-primary), 0.1);
    border-color: rgba(var(--v-theme-primary), 0.3);
    transform: translateY(-2px);
  }
  
  &:active {
    cursor: grabbing;
    transform: scale(0.95);
  }
}

.sensor-name {
  font-size: 11px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

// Room Info Card
.room-info-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.05) 0%, transparent 100%);
}

.room-stats {
  display: flex;
  gap: 16px;
  
  .stat {
    display: flex;
    align-items: center;
    font-size: 13px;
    color: rgba(var(--v-theme-on-surface), 0.7);
  }
}

.room-sensors {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  padding-top: 12px;
}

.sensor-list-item {
  border-radius: 8px;
  margin-bottom: 4px;
  
  &:hover {
    background: rgba(var(--v-theme-surface-variant), 0.5);
  }
}

.sensor-value {
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

// Legend
.legend-card {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  
  &.room-classroom { background: rgba(66, 133, 244, 0.5); }
  &.room-lab { background: rgba(156, 39, 176, 0.5); }
  &.room-meeting { background: rgba(255, 152, 0, 0.5); }
  &.room-office { background: rgba(76, 175, 80, 0.5); }
  &.room-common { background: rgba(0, 188, 212, 0.5); }
  &.room-utility { background: rgba(158, 158, 158, 0.5); }
}

// Position dialog
.position-preview {
  display: flex;
  justify-content: center;
}

.preview-room {
  width: 280px;
  height: 200px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border: 2px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 8px;
  position: relative;
  cursor: crosshair;
  overflow: hidden;
}

.preview-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    linear-gradient(rgba(var(--v-theme-on-surface), 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--v-theme-on-surface), 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

.position-marker {
  position: absolute;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translate(-50%, -50%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: left 0.15s ease, top 0.15s ease;
  z-index: 10;
}

.preview-label {
  position: absolute;
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  
  &.top { top: 8px; left: 50%; transform: translateX(-50%); }
  &.bottom { bottom: 8px; left: 50%; transform: translateX(-50%); }
  &.left { left: 8px; top: 50%; transform: translateY(-50%) rotate(-90deg); }
  &.right { right: 8px; top: 50%; transform: translateY(-50%) rotate(90deg); }
}

.quick-positions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
