<template>
  <div class="building-3d-view">
    <!-- Header Controls -->
    <v-card class="controls-card mb-4">
      <v-card-text class="d-flex align-center justify-space-between flex-wrap ga-4">
        <div class="d-flex align-center ga-4">
          <div class="view-icon">
            <v-icon size="32" color="primary">mdi-cube-scan</v-icon>
          </div>
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Bâtiment Orion</h1>
            <p class="text-body-2 text-medium-emphasis mb-0">
              CESI Nancy • {{ currentFloorRooms.length }} salles • {{ totalSensors }} capteurs
            </p>
          </div>
        </div>
        
        <div class="d-flex align-center ga-2 flex-wrap">
          <!-- Floor selector -->
          <v-btn-toggle v-model="selectedFloor" mandatory density="compact" color="primary" class="floor-toggle">
            <v-btn v-for="floor in floors" :key="floor.id" :value="floor.id" size="small">
              <v-icon start size="16">mdi-layers</v-icon>
              {{ floor.id }}
            </v-btn>
          </v-btn-toggle>
          
          <!-- View mode -->
          <v-btn-toggle v-model="viewMode" mandatory density="compact" class="ml-2">
            <v-btn value="normal" size="small">
              <v-icon size="18">mdi-eye</v-icon>
              <v-tooltip activator="parent" location="bottom">Vue normale</v-tooltip>
            </v-btn>
            <v-btn value="heatmap" size="small">
              <v-icon size="18">mdi-thermometer</v-icon>
              <v-tooltip activator="parent" location="bottom">Heatmap température</v-tooltip>
            </v-btn>
            <v-btn value="sensors" size="small">
              <v-icon size="18">mdi-chip</v-icon>
              <v-tooltip activator="parent" location="bottom">Vue capteurs</v-tooltip>
            </v-btn>
          </v-btn-toggle>
          
          <!-- Camera controls -->
          <div class="camera-controls ml-2">
            <v-btn icon variant="text" size="small" @click="setCameraTop">
              <v-icon>mdi-arrow-up-bold-box</v-icon>
              <v-tooltip activator="parent" location="bottom">Vue dessus</v-tooltip>
            </v-btn>
            <v-btn icon variant="text" size="small" @click="setCameraFront">
              <v-icon>mdi-arrow-right-bold-box</v-icon>
              <v-tooltip activator="parent" location="bottom">Vue face</v-tooltip>
            </v-btn>
            <v-btn icon variant="text" size="small" @click="resetCamera">
              <v-icon>mdi-camera-retake</v-icon>
              <v-tooltip activator="parent" location="bottom">Réinitialiser</v-tooltip>
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- 3D Canvas -->
      <v-col cols="12" :lg="selectedRoom ? 8 : 9">
        <v-card class="canvas-card">
          <div 
            ref="canvasContainer" 
            class="canvas-container"
            @click="handleCanvasClick"
          >
            <!-- Loading overlay -->
            <div v-if="loading" class="loading-overlay">
              <div class="loading-content">
                <div class="loading-cube">
                  <div class="cube-face front"></div>
                  <div class="cube-face back"></div>
                  <div class="cube-face right"></div>
                  <div class="cube-face left"></div>
                  <div class="cube-face top"></div>
                  <div class="cube-face bottom"></div>
                </div>
                <p class="mt-6 text-body-1">Chargement du Digital Twin...</p>
                <v-progress-linear indeterminate color="primary" class="mt-2" style="width: 200px" />
              </div>
            </div>
            
            <!-- Instructions overlay -->
            <div class="instructions-overlay" v-if="!loading && !selectedRoom && !repositionMode">
              <v-chip size="small" color="surface" variant="flat" class="instruction-chip">
                <v-icon start size="14">mdi-gesture-swipe</v-icon>
                Glisser pour tourner
              </v-chip>
              <v-chip size="small" color="surface" variant="flat" class="instruction-chip">
                <v-icon start size="14">mdi-magnify</v-icon>
                Molette pour zoomer
              </v-chip>
              <v-chip size="small" color="surface" variant="flat" class="instruction-chip">
                <v-icon start size="14">mdi-cursor-pointer</v-icon>
                Cliquer sur une salle
              </v-chip>
              <v-chip size="small" color="surface" variant="flat" class="instruction-chip">
                <v-icon start size="14">mdi-chip</v-icon>
                Cliquer sur un capteur pour le déplacer
              </v-chip>
            </div>

            <!-- Reposition mode overlay -->
            <div class="reposition-overlay" v-if="repositionMode">
              <v-card class="reposition-card" color="info" variant="elevated">
                <v-card-text class="d-flex align-center pa-3">
                  <v-icon start class="pulse-icon">mdi-crosshairs-gps</v-icon>
                  <div>
                    <div class="font-weight-bold">Mode repositionnement</div>
                    <div class="text-caption">Cliquez dans la salle pour placer le capteur</div>
                  </div>
                  <v-btn 
                    icon 
                    variant="text" 
                    size="small" 
                    class="ml-4"
                    @click="cancelReposition"
                  >
                    <v-icon>mdi-close</v-icon>
                  </v-btn>
                </v-card-text>
              </v-card>
            </div>

            <!-- Compass -->
            <div class="compass" v-if="!loading">
              <div class="compass-ring">
                <span class="compass-n">N</span>
                <span class="compass-e">E</span>
                <span class="compass-s">S</span>
                <span class="compass-w">O</span>
              </div>
            </div>

            <!-- Mini stats -->
            <div class="mini-stats" v-if="!loading">
              <div class="mini-stat">
                <v-icon size="16" color="error">mdi-thermometer</v-icon>
                <span>{{ avgTemperature }}°C</span>
              </div>
              <div class="mini-stat">
                <v-icon size="16" color="info">mdi-water-percent</v-icon>
                <span>{{ avgHumidity }}%</span>
              </div>
              <div class="mini-stat" v-if="alertCount > 0">
                <v-icon size="16" color="warning">mdi-alert</v-icon>
                <span>{{ alertCount }}</span>
              </div>
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- Sidebar -->
      <v-col cols="12" :lg="selectedRoom ? 4 : 3">
        <!-- Selected Room Info (expanded) -->
        <v-card v-if="selectedRoom" class="room-info-card mb-4">
          <div class="room-header" :style="{ background: getRoomHeaderGradient(selectedRoom.type) }">
            <v-btn icon variant="text" size="small" class="close-btn" @click="deselectRoom">
              <v-icon>mdi-close</v-icon>
            </v-btn>
            <div class="room-id-badge">{{ selectedRoom.id }}</div>
            <h2 class="room-title">{{ selectedRoom.name }}</h2>
            <div class="room-meta">
              <v-chip size="small" :color="getRoomTypeColor(selectedRoom.type)" variant="flat">
                <v-icon start size="14">{{ getRoomTypeIcon(selectedRoom.type) }}</v-icon>
                {{ getRoomTypeLabel(selectedRoom.type) }}
              </v-chip>
              <v-chip size="small" variant="tonal" class="ml-2">
                <v-icon start size="14">mdi-account-group</v-icon>
                {{ selectedRoom.capacity || '?' }} places
              </v-chip>
            </div>
          </div>
          
          <v-card-text class="pa-4">
            <!-- Sensors in room -->
            <div class="section-title mb-3">
              <v-icon start size="18">mdi-chip</v-icon>
              Capteurs ({{ roomSensors.length }})
            </div>
            
            <div v-if="roomSensors.length > 0" class="sensors-grid">
              <div 
                v-for="sensor in roomSensors" 
                :key="sensor.id"
                class="sensor-card-3d"
                :class="{ 'active': sensor.status === 'ok' }"
              >
                <div class="sensor-icon-wrap" :style="{ background: getSensorColor(sensor.type) + '22' }">
                  <v-icon :color="getSensorColor(sensor.type)" size="24">
                    {{ getSensorIcon(sensor.type) }}
                  </v-icon>
                </div>
                <div class="sensor-details">
                  <span class="sensor-label">{{ getSensorTypeName(sensor.type) }}</span>
                  <span class="sensor-value-lg" :style="{ color: getSensorColor(sensor.type) }">
                    {{ formatSensorValue(sensor) }}
                  </span>
                </div>
                <v-btn
                  icon
                  variant="text"
                  size="x-small"
                  color="error"
                  class="delete-btn"
                  @click.stop="removeSensor(sensor.id)"
                >
                  <v-icon size="16">mdi-delete</v-icon>
                </v-btn>
              </div>
            </div>
            
            <div v-else class="no-sensors">
              <v-icon size="40" color="grey">mdi-chip-off</v-icon>
              <p class="text-body-2 text-medium-emphasis mt-2">Aucun capteur</p>
              <p class="text-caption text-medium-emphasis">Glissez un capteur ici</p>
            </div>

            <v-divider class="my-4" />
            
            <!-- Quick Actions -->
            <div class="section-title mb-3">
              <v-icon start size="18">mdi-lightning-bolt</v-icon>
              Actions rapides
            </div>
            
            <div class="actions-grid">
              <v-btn
                color="primary"
                variant="tonal"
                @click="openQRDialog"
                class="action-btn"
              >
                <v-icon start>mdi-qrcode</v-icon>
                QR Code
              </v-btn>
              <v-btn
                color="warning"
                variant="tonal"
                @click="openReportDialog"
                class="action-btn"
              >
                <v-icon start>mdi-alert-circle</v-icon>
                Signaler
              </v-btn>
              <v-btn
                color="info"
                variant="tonal"
                :to="`/room/${selectedRoom.id}`"
                class="action-btn"
              >
                <v-icon start>mdi-chart-line</v-icon>
                Historique
              </v-btn>
              <v-btn
                color="success"
                variant="tonal"
                @click="focusOnRoom"
                class="action-btn"
              >
                <v-icon start>mdi-target</v-icon>
                Centrer
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Legend -->
        <v-card class="legend-card">
          <v-card-title class="d-flex align-center">
            <v-icon start color="primary">mdi-map-legend</v-icon>
            Légende
          </v-card-title>
          <v-card-text>
            <!-- View mode specific legend -->
            <div v-if="viewMode === 'heatmap'" class="heatmap-legend">
              <p class="text-caption text-medium-emphasis mb-2">Température</p>
              <div class="legend-gradient"></div>
              <div class="legend-labels">
                <span>❄️ &lt;18°C</span>
                <span>✓ 20-22°C</span>
                <span>🔥 &gt;26°C</span>
              </div>
            </div>
            
            <div v-else class="type-legend">
              <div 
                v-for="(color, type) in roomTypeColors" 
                :key="type"
                class="legend-item"
              >
                <div class="legend-color" :style="{ background: color }"></div>
                <span>{{ getRoomTypeLabel(type) }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- QR Code Dialog -->
    <QRCodeDialog
      v-model="showQRDialog"
      :room="selectedRoom"
    />

    <!-- Report Issue Dialog -->
    <ReportIssueDialog
      v-model="showReportDialog"
      :room="selectedRoom"
      @reported="handleReportSubmitted"
    />

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="bottom right">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useBuildingStore } from '@/stores/building'
import { useAlertsStore } from '@/stores/alerts'
import { storeToRefs } from 'pinia'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import QRCodeDialog from '@/components/QRCodeDialog.vue'
import ReportIssueDialog from '@/components/ReportIssueDialog.vue'

const buildingStore = useBuildingStore()
const alertsStore = useAlertsStore()
const { floors, currentFloorRooms, sensors: buildingSensors } = storeToRefs(buildingStore)
const { activeAlerts } = storeToRefs(alertsStore)

// State
const canvasContainer = ref(null)
const loading = ref(true)
const selectedFloor = ref('R+1')
const selectedRoom = ref(null)
const viewMode = ref('normal')
const showQRDialog = ref(false)
const showReportDialog = ref(false)
const snackbar = ref({ show: false, text: '', color: 'success' })

// Sensor repositioning mode
const repositionMode = ref(false)
const selectedSensorForReposition = ref(null)

// Three.js objects
let scene, camera, renderer, controls
let roomMeshes = {}
let sensorMeshes = {}
let labelSprites = {}
let raycaster, mouse
let animationId

// Room type colors
const roomTypeColors = {
  classroom: '#4285f4',
  lab: '#9c27b0',
  meeting: '#ff9800',
  office: '#4caf50',
  common: '#00bcd4',
  utility: '#9e9e9e'
}

// Computed
const roomSensors = computed(() => {
  if (!selectedRoom.value) return []
  return buildingStore.getRoomSensors(selectedRoom.value.id)
})

const totalSensors = computed(() => buildingSensors.value.length)

const avgTemperature = computed(() => {
  const temps = buildingSensors.value
    .filter(s => s.type === 'temperature' && s.value !== null)
    .map(s => s.value)
  if (temps.length === 0) return '--'
  return (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1)
})

const avgHumidity = computed(() => {
  const hums = buildingSensors.value
    .filter(s => s.type === 'humidity' && s.value !== null)
    .map(s => s.value)
  if (hums.length === 0) return '--'
  return Math.round(hums.reduce((a, b) => a + b, 0) / hums.length)
})

const alertCount = computed(() => activeAlerts.value.length)

// Initialize Three.js scene
function initScene() {
  if (!canvasContainer.value) return
  
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  
  // Scene with gradient background
  scene = new THREE.Scene()
  
  // Create gradient background
  const canvas = document.createElement('canvas')
  canvas.width = 2
  canvas.height = 512
  const ctx = canvas.getContext('2d')
  const gradient = ctx.createLinearGradient(0, 0, 0, 512)
  gradient.addColorStop(0, '#0f0f23')
  gradient.addColorStop(0.5, '#1a1a2e')
  gradient.addColorStop(1, '#16213e')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, 2, 512)
  
  const bgTexture = new THREE.CanvasTexture(canvas)
  scene.background = bgTexture
  scene.fog = new THREE.Fog(0x1a1a2e, 80, 200)
  
  // Camera
  camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000)
  camera.position.set(50, 40, 50)
  
  // Renderer with better quality and logarithmic depth buffer to prevent z-fighting
  renderer = new THREE.WebGLRenderer({ 
    antialias: true, 
    alpha: true,
    powerPreference: 'high-performance',
    logarithmicDepthBuffer: true
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  canvasContainer.value.appendChild(renderer.domElement)
  
  // Controls
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.maxPolarAngle = Math.PI / 2.05
  controls.minDistance = 15
  controls.maxDistance = 120
  controls.target.set(0, 0, 0)
  
  // Raycaster
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()
  
  // Add scene elements
  addLights()
  addGround()
  addBuildingBase()
  buildRooms()
  
  // Start animation
  animate()
  
  // Event listeners
  window.addEventListener('resize', onWindowResize)
  
  loading.value = false
}

function addLights() {
  // Ambient light
  const ambient = new THREE.AmbientLight(0xffffff, 0.5)
  scene.add(ambient)
  
  // Main directional light (sun)
  const sun = new THREE.DirectionalLight(0xffffff, 1)
  sun.position.set(40, 60, 30)
  sun.castShadow = true
  sun.shadow.mapSize.width = 4096
  sun.shadow.mapSize.height = 4096
  sun.shadow.camera.near = 0.5
  sun.shadow.camera.far = 200
  sun.shadow.camera.left = -60
  sun.shadow.camera.right = 60
  sun.shadow.camera.top = 60
  sun.shadow.camera.bottom = -60
  sun.shadow.bias = -0.0001
  scene.add(sun)
  
  // Fill light
  const fill = new THREE.DirectionalLight(0x00d4ff, 0.3)
  fill.position.set(-30, 20, -30)
  scene.add(fill)
  
  // Accent lights
  const accent1 = new THREE.PointLight(0x00ff9d, 0.8, 60)
  accent1.position.set(-25, 8, -25)
  scene.add(accent1)
  
  const accent2 = new THREE.PointLight(0xff006e, 0.5, 50)
  accent2.position.set(25, 8, 25)
  scene.add(accent2)
  
  // Hemisphere light for natural feel
  const hemi = new THREE.HemisphereLight(0x00d4ff, 0x1a1a2e, 0.4)
  scene.add(hemi)
}

function addGround() {
  // Ground plane first (at bottom)
  const groundGeo = new THREE.PlaneGeometry(120, 120)
  const groundMat = new THREE.MeshStandardMaterial({ 
    color: 0x1a1a2e,
    roughness: 0.85,
    metalness: 0.15,
    envMapIntensity: 0.5,
    depthWrite: true
  })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.5 // Lower the ground to avoid z-fighting
  ground.receiveShadow = true
  ground.renderOrder = 0
  scene.add(ground)
  
  // Grid helper above the ground
  const gridHelper = new THREE.GridHelper(120, 60, 0x00ff9d, 0x222233)
  gridHelper.position.y = 0.02 // Slightly above ground
  gridHelper.material.opacity = 0.4
  gridHelper.material.transparent = true
  gridHelper.material.depthWrite = false // Prevent z-fighting
  gridHelper.renderOrder = 1
  scene.add(gridHelper)
}

function addBuildingBase() {
  // Building foundation/outline
  const rooms = currentFloorRooms.value
  if (rooms.length === 0) return
  
  // Calculate building bounds
  let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity
  const scale = 0.35
  const offsetX = -35
  const offsetZ = -18
  
  rooms.forEach(room => {
    const x1 = room.x * scale + offsetX
    const x2 = (room.x + room.width) * scale + offsetX
    const z1 = room.y * scale + offsetZ
    const z2 = (room.y + room.height) * scale + offsetZ
    minX = Math.min(minX, x1)
    maxX = Math.max(maxX, x2)
    minZ = Math.min(minZ, z1)
    maxZ = Math.max(maxZ, z2)
  })
  
  // Building outline - positioned clearly above grid
  const outlineGeo = new THREE.BoxGeometry(maxX - minX + 2, 0.3, maxZ - minZ + 2)
  const outlineMat = new THREE.MeshStandardMaterial({
    color: 0x00ff9d,
    roughness: 0.5,
    metalness: 0.8,
    emissive: 0x00ff9d,
    emissiveIntensity: 0.1
  })
  const outline = new THREE.Mesh(outlineGeo, outlineMat)
  outline.position.set((minX + maxX) / 2, 0.2, (minZ + maxZ) / 2) // Above grid to avoid z-fighting
  outline.receiveShadow = true
  outline.renderOrder = 2
  scene.add(outline)
}

function buildRooms() {
  // Clear existing
  clearScene()
  
  const rooms = currentFloorRooms.value
  const scale = 0.35
  const offsetX = -35
  const offsetZ = -18
  const baseHeight = 4
  
  rooms.forEach((room, index) => {
    // Room dimensions
    const width = room.width * scale
    const depth = room.height * scale
    const height = baseHeight + (room.type === 'common' ? 1 : 0)
    
    // Create room geometry with beveled edges
    const geometry = new THREE.BoxGeometry(width - 0.2, height, depth - 0.2)
    
    // Material based on view mode
    const color = getRoomColor(room)
    const material = new THREE.MeshStandardMaterial({
      color: color,
      roughness: 0.6,
      metalness: 0.3,
      transparent: viewMode.value === 'sensors',
      opacity: viewMode.value === 'sensors' ? 0.4 : 1
    })
    
    const mesh = new THREE.Mesh(geometry, material)
    
    // Position
    const x = (room.x + room.width / 2) * scale + offsetX
    const z = (room.y + room.height / 2) * scale + offsetZ
    mesh.position.set(x, height / 2, z)
    
    mesh.castShadow = true
    mesh.receiveShadow = true
    mesh.userData.room = room
    mesh.userData.baseColor = color
    
    scene.add(mesh)
    roomMeshes[room.id] = mesh
    
    // Add edge glow
    addRoomEdges(mesh, room)
    
    // Add label
    addRoomLabel(room, { x, y: height + 0.8, z }, width)
    
    // Add sensors if in sensor view
    if (viewMode.value === 'sensors') {
      addSensorMarkers(room, { x, y: height, z })
    }
  })
}

function addRoomEdges(mesh, room) {
  const edges = new THREE.EdgesGeometry(mesh.geometry)
  const lineMaterial = new THREE.LineBasicMaterial({ 
    color: selectedRoom.value?.id === room.id ? 0x00ff9d : 0x333366,
    linewidth: 1,
    transparent: true,
    opacity: 0.6
  })
  const line = new THREE.LineSegments(edges, lineMaterial)
  line.position.copy(mesh.position)
  scene.add(line)
}

function addRoomLabel(room, position, roomWidth) {
  // Check if this is a corridor (long room where label should stay fixed)
  const isCorridor = room.id.includes('HALL') || (room.width / room.height > 4)
  
  // Create high-quality canvas label
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const pixelRatio = 2
  
  canvas.width = 512 * pixelRatio
  canvas.height = 128 * pixelRatio
  ctx.scale(pixelRatio, pixelRatio)
  
  // Background with gradient
  const bgGradient = ctx.createLinearGradient(0, 0, 0, 64)
  bgGradient.addColorStop(0, 'rgba(0, 0, 0, 0.9)')
  bgGradient.addColorStop(1, 'rgba(26, 26, 46, 0.9)')
  
  // Rounded rectangle background
  const padding = 20
  const bgWidth = 512 - padding * 2
  const bgHeight = 90
  ctx.fillStyle = bgGradient
  roundRect(ctx, padding, 10, bgWidth, bgHeight, 12)
  ctx.fill()
  
  // Border
  ctx.strokeStyle = '#00ff9d'
  ctx.lineWidth = 2
  roundRect(ctx, padding, 10, bgWidth, bgHeight, 12)
  ctx.stroke()
  
  // Room ID
  ctx.font = 'bold 36px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#00ff9d'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.fillText(room.id, 256, 22)
  
  // Room name (truncated if needed)
  ctx.font = '20px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#ffffff'
  let name = room.name
  if (ctx.measureText(name).width > bgWidth - 40) {
    while (ctx.measureText(name + '...').width > bgWidth - 40 && name.length > 0) {
      name = name.slice(0, -1)
    }
    name += '...'
  }
  ctx.fillText(name, 256, 62)
  
  const texture = new THREE.CanvasTexture(canvas)
  texture.minFilter = THREE.LinearFilter
  texture.magFilter = THREE.LinearFilter
  
  const labelScale = Math.max(4, roomWidth * 0.8)
  
  if (isCorridor) {
    // For corridors: use a fixed Mesh that doesn't rotate with camera
    const planeGeo = new THREE.PlaneGeometry(labelScale, labelScale * 0.25)
    const planeMat = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      side: THREE.DoubleSide,
      depthTest: false
    })
    const labelMesh = new THREE.Mesh(planeGeo, planeMat)
    
    // Position the label flat on top of the corridor, facing up
    labelMesh.position.set(position.x, position.y, position.z)
    labelMesh.rotation.x = -Math.PI / 2 // Rotate to be parallel to floor
    labelMesh.renderOrder = 999
    
    scene.add(labelMesh)
    labelSprites[room.id] = labelMesh
  } else {
    // For regular rooms: use Sprite that follows camera
    const spriteMaterial = new THREE.SpriteMaterial({ 
      map: texture,
      transparent: true,
      depthTest: false
    })
    const sprite = new THREE.Sprite(spriteMaterial)
    
    sprite.position.set(position.x, position.y, position.z)
    sprite.scale.set(labelScale, labelScale * 0.25, 1)
    sprite.renderOrder = 999
    
    scene.add(sprite)
    labelSprites[room.id] = sprite
  }
}

function addSensorMarkers(room, position) {
  const sensors = buildingStore.getRoomSensors(room.id)
  if (sensors.length === 0) return
  
  sensors.forEach((sensor, i) => {
    const angle = (i / sensors.length) * Math.PI * 2
    const radius = 1.5
    
    // Sensor sphere
    const geometry = new THREE.SphereGeometry(0.4, 16, 16)
    const color = new THREE.Color(getSensorColor(sensor.type))
    const material = new THREE.MeshStandardMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: 0.5,
      metalness: 0.8,
      roughness: 0.2
    })
    
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(
      position.x + Math.cos(angle) * radius,
      position.y + 0.5,
      position.z + Math.sin(angle) * radius
    )
    mesh.userData.sensor = sensor
    
    scene.add(mesh)
    sensorMeshes[sensor.id] = mesh
    
    // Pulsing ring
    const ringGeo = new THREE.RingGeometry(0.5, 0.6, 32)
    const ringMat = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.5,
      side: THREE.DoubleSide
    })
    const ring = new THREE.Mesh(ringGeo, ringMat)
    ring.position.copy(mesh.position)
    ring.position.y += 0.1
    ring.rotation.x = -Math.PI / 2
    ring.userData.pulse = true
    ring.userData.baseScale = 1
    scene.add(ring)
  })
}

function clearScene() {
  // Remove room meshes
  Object.values(roomMeshes).forEach(mesh => {
    scene.remove(mesh)
    mesh.geometry.dispose()
    mesh.material.dispose()
  })
  roomMeshes = {}
  
  // Remove labels
  Object.values(labelSprites).forEach(sprite => {
    scene.remove(sprite)
    sprite.material.map.dispose()
    sprite.material.dispose()
  })
  labelSprites = {}
  
  // Remove sensor meshes
  Object.values(sensorMeshes).forEach(mesh => {
    scene.remove(mesh)
    mesh.geometry.dispose()
    mesh.material.dispose()
  })
  sensorMeshes = {}
  
  // Remove lines and other objects
  const toRemove = []
  scene.traverse(obj => {
    if (obj instanceof THREE.LineSegments || obj.userData.pulse) {
      toRemove.push(obj)
    }
  })
  toRemove.forEach(obj => scene.remove(obj))
}

function getRoomColor(room) {
  if (viewMode.value === 'heatmap') {
    const sensors = buildingStore.getRoomSensors(room.id)
    const tempSensor = sensors.find(s => s.type === 'temperature')
    
    if (!tempSensor || tempSensor.value === null) {
      return 0x555555
    }
    
    const temp = tempSensor.value
    // Gradient from blue to green to red
    if (temp < 16) return 0x2563eb
    if (temp < 18) return 0x3b82f6
    if (temp < 20) return 0x22c55e
    if (temp < 22) return 0x4ade80
    if (temp < 24) return 0x84cc16
    if (temp < 26) return 0xeab308
    if (temp < 28) return 0xf97316
    return 0xef4444
  }
  
  return parseInt(roomTypeColors[room.type]?.replace('#', '0x') || '0x666666')
}

function getRoomHeaderGradient(type) {
  const color = roomTypeColors[type] || '#666666'
  return `linear-gradient(135deg, ${color}dd 0%, ${color}88 100%)`
}

function handleCanvasClick(event) {
  if (!canvasContainer.value || loading.value) return
  
  const rect = canvasContainer.value.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  
  raycaster.setFromCamera(mouse, camera)
  
  // Check if we're in reposition mode
  if (repositionMode.value && selectedSensorForReposition.value) {
    handleSensorReposition(event)
    return
  }
  
  // Check if clicking on a sensor first
  const sensorMeshList = Object.values(sensorMeshes)
  const sensorIntersects = raycaster.intersectObjects(sensorMeshList)
  
  if (sensorIntersects.length > 0) {
    const clickedSensor = sensorIntersects[0].object.userData.sensor
    if (clickedSensor) {
      startSensorReposition(clickedSensor)
      return
    }
  }
  
  // Otherwise check rooms
  const meshes = Object.values(roomMeshes)
  const intersects = raycaster.intersectObjects(meshes)
  
  if (intersects.length > 0) {
    const clickedRoom = intersects[0].object.userData.room
    selectRoom(clickedRoom)
  } else {
    // Clicked outside - cancel reposition mode
    cancelReposition()
  }
}

function selectRoom(room) {
  selectedRoom.value = room
  
  // Update room highlighting
  Object.entries(roomMeshes).forEach(([id, mesh]) => {
    if (id === room.id) {
      mesh.material.emissive = new THREE.Color(0x00ff9d)
      mesh.material.emissiveIntensity = 0.3
    } else {
      mesh.material.emissive = new THREE.Color(0x000000)
      mesh.material.emissiveIntensity = 0
    }
  })
}

function deselectRoom() {
  selectedRoom.value = null
  Object.values(roomMeshes).forEach(mesh => {
    mesh.material.emissive = new THREE.Color(0x000000)
    mesh.material.emissiveIntensity = 0
  })
}

function focusOnRoom() {
  if (!selectedRoom.value) return
  
  const mesh = roomMeshes[selectedRoom.value.id]
  if (!mesh) return
  
  const targetPosition = mesh.position.clone()
  controls.target.copy(targetPosition)
  
  camera.position.set(
    targetPosition.x + 15,
    targetPosition.y + 12,
    targetPosition.z + 15
  )
}

// Camera presets
function setCameraTop() {
  camera.position.set(0, 70, 0.1)
  controls.target.set(0, 0, 0)
}

function setCameraFront() {
  camera.position.set(0, 20, 60)
  controls.target.set(0, 0, 0)
}

function resetCamera() {
  camera.position.set(50, 40, 50)
  controls.target.set(0, 0, 0)
}

// Sensor repositioning functions
function startSensorReposition(sensor) {
  selectedSensorForReposition.value = sensor
  repositionMode.value = true
  
  // Highlight the sensor
  const mesh = sensorMeshes[sensor.id]
  if (mesh) {
    mesh.material.emissive = new THREE.Color(0x00ff00)
    mesh.material.emissiveIntensity = 0.5
  }
  
  snackbar.value = {
    show: true,
    text: `Cliquez dans la salle pour repositionner "${sensor.name || sensor.type}"`,
    color: 'info'
  }
}

function handleSensorReposition(event) {
  if (!selectedSensorForReposition.value) return
  
  const sensor = selectedSensorForReposition.value
  const sensorRoom = buildingStore.getRoomById(sensor.room_id)
  
  if (!sensorRoom) {
    cancelReposition()
    return
  }
  
  // Get intersection with the room floor
  const roomMesh = roomMeshes[sensor.room_id]
  if (!roomMesh) {
    cancelReposition()
    return
  }
  
  const intersects = raycaster.intersectObject(roomMesh)
  
  if (intersects.length > 0) {
    const point = intersects[0].point
    
    // Convert 3D position to relative position within room (0-1)
    const roomX = sensorRoom.x / 10
    const roomZ = sensorRoom.y / 10
    const roomWidth = sensorRoom.width / 10
    const roomDepth = sensorRoom.height / 10
    
    // Calculate relative position (0-1)
    const relX = (point.x - roomX) / roomWidth
    const relZ = (point.z - roomZ) / roomDepth
    
    // Clamp to room bounds
    const clampedX = Math.max(0.1, Math.min(0.9, relX))
    const clampedZ = Math.max(0.1, Math.min(0.9, relZ))
    
    // Update sensor position via store (syncs to backend + other users)
    buildingStore.updateSensorPosition(sensor.id, clampedX, clampedZ, 0)
    
    // Update 3D mesh position immediately for feedback
    const sensorMesh = sensorMeshes[sensor.id]
    if (sensorMesh) {
      sensorMesh.position.x = roomX + clampedX * roomWidth
      sensorMesh.position.z = roomZ + clampedZ * roomDepth
    }
    
    snackbar.value = {
      show: true,
      text: `Capteur repositionné !`,
      color: 'success'
    }
  }
  
  cancelReposition()
}

function cancelReposition() {
  // Remove highlight from sensor
  if (selectedSensorForReposition.value) {
    const mesh = sensorMeshes[selectedSensorForReposition.value.id]
    if (mesh) {
      mesh.material.emissive = new THREE.Color(0x000000)
      mesh.material.emissiveIntensity = 0
    }
  }
  
  repositionMode.value = false
  selectedSensorForReposition.value = null
}

// Dialogs
function openQRDialog() {
  if (selectedRoom.value) {
    showQRDialog.value = true
  }
}

function openReportDialog() {
  if (selectedRoom.value) {
    showReportDialog.value = true
  }
}

function handleReportSubmitted(report) {
  snackbar.value = {
    show: true,
    text: `Signalement envoyé pour ${report.room_id}`,
    color: 'success'
  }
}

// Animation loop
function animate() {
  animationId = requestAnimationFrame(animate)
  
  controls.update()
  
  // Animate pulsing rings
  const time = Date.now() * 0.002
  scene.traverse(obj => {
    if (obj.userData.pulse) {
      const scale = 1 + Math.sin(time) * 0.2
      obj.scale.set(scale, scale, 1)
      obj.material.opacity = 0.3 + Math.sin(time) * 0.2
    }
  })
  
  renderer.render(scene, camera)
}

function onWindowResize() {
  if (!canvasContainer.value) return
  
  const width = canvasContainer.value.clientWidth
  const height = canvasContainer.value.clientHeight
  
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// Helper functions
function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius)
  ctx.lineTo(x + width, y + height - radius)
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height)
  ctx.lineTo(x + radius, y + height)
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius)
  ctx.lineTo(x, y + radius)
  ctx.quadraticCurveTo(x, y, x + radius, y)
  ctx.closePath()
}

function getSensorColor(type) {
  const colors = {
    temperature: '#ff6b6b',
    humidity: '#4ecdc4',
    presence: '#fbbf24',
    co2: '#22c55e',
    light: '#f59e0b'
  }
  return colors[type] || '#888888'
}

function getSensorIcon(type) {
  const icons = {
    temperature: 'mdi-thermometer',
    humidity: 'mdi-water-percent',
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
    presence: 'Présence',
    co2: 'CO2',
    light: 'Luminosité'
  }
  return names[type] || type
}

function formatSensorValue(sensor) {
  if (sensor.value === null || sensor.value === undefined) return '--'
  if (sensor.type === 'temperature') return `${sensor.value.toFixed(1)}°C`
  if (sensor.type === 'humidity') return `${Math.round(sensor.value)}%`
  if (sensor.type === 'presence') return sensor.value ? 'Détecté' : 'Vide'
  if (sensor.type === 'co2') return `${Math.round(sensor.value)} ppm`
  if (sensor.type === 'light') return `${Math.round(sensor.value)} lux`
  return sensor.value
}

function getRoomTypeColor(type) {
  return roomTypeColors[type] || '#666666'
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

function getRoomTypeLabel(type) {
  const labels = {
    classroom: 'Salle de cours',
    lab: 'Laboratoire',
    meeting: 'Réunion',
    office: 'Bureau',
    common: 'Espace commun',
    utility: 'Technique'
  }
  return labels[type] || type
}

// Watchers
watch(selectedFloor, () => {
  buildingStore.setFloor(selectedFloor.value)
  nextTick(() => {
    clearScene()
    addBuildingBase()
    buildRooms()
  })
})

watch(viewMode, () => {
  nextTick(() => {
    clearScene()
    addBuildingBase()
    buildRooms()
  })
})

// Lifecycle
onMounted(() => {
  setTimeout(initScene, 100)
})

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<style scoped lang="scss">
.building-3d-view {
  height: 100%;
}

.controls-card {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(0,0,0,0) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  backdrop-filter: blur(10px);
}

.view-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.2) 0%, rgba(var(--v-theme-primary), 0.05) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.floor-toggle {
  :deep(.v-btn) {
    text-transform: none;
  }
}

.canvas-card {
  background: #1a1a2e;
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.canvas-container {
  width: 100%;
  height: 650px;
  position: relative;
  cursor: grab;
  
  &:active {
    cursor: grabbing;
  }
  
  canvas {
    display: block;
  }
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
  z-index: 10;
  
  .loading-content {
    text-align: center;
    color: white;
  }
}

// Animated loading cube
.loading-cube {
  width: 60px;
  height: 60px;
  position: relative;
  transform-style: preserve-3d;
  animation: rotate 2s infinite linear;
  margin: 0 auto;
  
  .cube-face {
    position: absolute;
    width: 60px;
    height: 60px;
    border: 2px solid #00ff9d;
    background: rgba(0, 255, 157, 0.1);
  }
  
  .front  { transform: translateZ(30px); }
  .back   { transform: translateZ(-30px) rotateY(180deg); }
  .right  { transform: translateX(30px) rotateY(90deg); }
  .left   { transform: translateX(-30px) rotateY(-90deg); }
  .top    { transform: translateY(-30px) rotateX(90deg); }
  .bottom { transform: translateY(30px) rotateX(-90deg); }
}

@keyframes rotate {
  from { transform: rotateX(-30deg) rotateY(0); }
  to { transform: rotateX(-30deg) rotateY(360deg); }
}

.instructions-overlay {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  z-index: 5;
  max-width: 90%;
  
  .instruction-chip {
    backdrop-filter: blur(10px);
    background: rgba(0, 0, 0, 0.7) !important;
    border: 1px solid rgba(0, 255, 157, 0.3);
    font-size: 11px;
  }
}

.reposition-overlay {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  
  .reposition-card {
    backdrop-filter: blur(10px);
    animation: pulse-border 1.5s infinite;
  }
  
  .pulse-icon {
    animation: pulse-scale 1s infinite;
  }
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.4); }
  50% { box-shadow: 0 0 0 10px rgba(33, 150, 243, 0); }
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.compass {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 5;
  
  .compass-ring {
    width: 50px;
    height: 50px;
    border: 2px solid rgba(0, 255, 157, 0.5);
    border-radius: 50%;
    position: relative;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(5px);
    
    span {
      position: absolute;
      font-size: 10px;
      font-weight: bold;
      color: #00ff9d;
      
      &.compass-n { top: 4px; left: 50%; transform: translateX(-50%); }
      &.compass-s { bottom: 4px; left: 50%; transform: translateX(-50%); opacity: 0.5; }
      &.compass-e { right: 6px; top: 50%; transform: translateY(-50%); opacity: 0.5; }
      &.compass-w { left: 6px; top: 50%; transform: translateY(-50%); opacity: 0.5; }
    }
  }
}

.mini-stats {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 12px;
  z-index: 5;
  
  .mini-stat {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
}

// Room info card
.room-info-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 20px;
  overflow: hidden;
}

.room-header {
  padding: 20px;
  color: white;
  position: relative;
  
  .close-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    color: white;
  }
  
  .room-id-badge {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  
  .room-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 12px;
  }
  
  .room-meta {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.sensors-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sensor-card-3d {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  position: relative;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(var(--v-theme-surface-variant), 0.5);
    
    .delete-btn {
      opacity: 1;
    }
  }
  
  &.active {
    border-left: 3px solid rgb(var(--v-theme-success));
  }
  
  .sensor-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .sensor-details {
    flex: 1;
    
    .sensor-label {
      display: block;
      font-size: 12px;
      color: rgba(var(--v-theme-on-surface), 0.6);
    }
    
    .sensor-value-lg {
      font-size: 20px;
      font-weight: 700;
    }
  }
  
  .delete-btn {
    opacity: 0;
    transition: opacity 0.2s;
  }
}

.no-sensors {
  text-align: center;
  padding: 24px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 12px;
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.1);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  
  .action-btn {
    text-transform: none;
    font-weight: 500;
  }
}

// Sensor palette
.sensor-palette-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.sensor-palette {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.palette-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  cursor: grab;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  
  &:hover {
    background: rgba(var(--v-theme-primary), 0.1);
    border-color: rgba(var(--v-theme-primary), 0.3);
    transform: translateY(-2px);
  }
  
  &:active {
    cursor: grabbing;
    transform: scale(0.95);
  }
  
  .palette-label {
    font-size: 10px;
    text-align: center;
    color: rgba(var(--v-theme-on-surface), 0.7);
  }
}

// Legend
.legend-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.heatmap-legend {
  .legend-gradient {
    height: 16px;
    border-radius: 8px;
    background: linear-gradient(90deg, 
      #2563eb 0%,
      #22c55e 35%,
      #84cc16 50%,
      #eab308 65%,
      #ef4444 100%
    );
  }
  
  .legend-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 11px;
    color: rgba(var(--v-theme-on-surface), 0.7);
  }
}

.type-legend {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  
  .legend-color {
    width: 16px;
    height: 16px;
    border-radius: 4px;
  }
}
</style>
