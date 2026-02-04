import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useBuildingStore = defineStore('building', () => {
  // Current floor
  const currentFloor = ref('RDC')
  
  // Loading state
  const loading = ref(false)
  
  // Building floors definition (3 levels: RDC, R+1, R+2)
  const floors = ref([
    { id: 'RDC', name: 'Rez-de-chaussée', level: 0 },
    { id: 'R+1', name: 'Premier étage', level: 1 },
    { id: 'R+2', name: 'Deuxième étage', level: 2 }
  ])

  // Rooms definition based on real Orion building plan (CESI Nancy)
  const rooms = ref([
    // ============ RDC - Rez-de-chaussée ============
    { id: 'X001', name: 'Accueil CESI', floor: 'RDC', x: 4, y: 8, width: 20, height: 22, type: 'common', capacity: 10, area: 29 },
    { id: 'X002', name: 'Bureau', floor: 'RDC', x: 26, y: 8, width: 16, height: 22, type: 'office', capacity: 4, area: 19 },
    { id: 'X003', name: 'Salle', floor: 'RDC', x: 44, y: 8, width: 20, height: 22, type: 'classroom', capacity: 15, area: 34 },
    { id: 'X004', name: 'Bureau', floor: 'RDC', x: 66, y: 8, width: 16, height: 22, type: 'office', capacity: 4, area: 12 },
    { id: 'X005', name: 'Salle', floor: 'RDC', x: 84, y: 8, width: 20, height: 22, type: 'classroom', capacity: 15, area: 30 },
    { id: 'X006', name: 'Salle', floor: 'RDC', x: 106, y: 8, width: 20, height: 22, type: 'classroom', capacity: 12, area: 27 },
    { id: 'X007', name: 'Salle 03', floor: 'RDC', x: 128, y: 8, width: 24, height: 22, type: 'classroom', capacity: 20, area: 38 },
    { id: 'X008', name: 'Détente élèves', floor: 'RDC', x: 156, y: 8, width: 38, height: 74, type: 'common', capacity: 30, area: 120 },
    { id: 'HALL_CESI', name: 'Hall CESI', floor: 'RDC', x: 4, y: 32, width: 20, height: 22, type: 'common', capacity: 20, area: 20 },
    { id: 'SAS', name: 'SAS', floor: 'RDC', x: 4, y: 56, width: 12, height: 18, type: 'common', capacity: 5, area: 13 },
    { id: 'ASC_RDC', name: 'Asc', floor: 'RDC', x: 18, y: 56, width: 10, height: 14, type: 'utility', capacity: 0, area: 5 },
    { id: 'X010', name: 'Elec', floor: 'RDC', x: 30, y: 56, width: 12, height: 18, type: 'utility', capacity: 0, area: 8 },
    { id: 'CTA', name: 'CTA', floor: 'RDC', x: 44, y: 56, width: 16, height: 22, type: 'utility', capacity: 0, area: 18 },
    { id: 'LOCAL_TECH', name: 'Local Tech', floor: 'RDC', x: 62, y: 56, width: 18, height: 22, type: 'utility', capacity: 0, area: 18 },
    { id: 'REPO_RDC', name: 'Repro', floor: 'RDC', x: 82, y: 56, width: 12, height: 16, type: 'utility', capacity: 2, area: 8 },
    { id: 'WCF_RDC', name: 'WC F', floor: 'RDC', x: 96, y: 56, width: 12, height: 16, type: 'utility', capacity: 0, area: 10 },
    { id: 'WCH_RDC', name: 'WC H', floor: 'RDC', x: 110, y: 56, width: 12, height: 16, type: 'utility', capacity: 0, area: 13 },
    { id: 'RGT', name: 'Rgt', floor: 'RDC', x: 124, y: 56, width: 12, height: 16, type: 'utility', capacity: 0, area: 6 },
    { id: 'X009', name: 'Rangement', floor: 'RDC', x: 138, y: 56, width: 16, height: 22, type: 'utility', capacity: 0, area: 26 },
    { id: 'HALL_RDC', name: 'Couloir', floor: 'RDC', x: 26, y: 32, width: 126, height: 22, type: 'common', capacity: 50, area: 150 },

    // ============ R+1 - Premier étage ============
    { id: 'X101', name: 'Open Space', floor: 'R+1', x: 4, y: 8, width: 24, height: 48, type: 'office', capacity: 40, area: 111 },
    { id: 'X102', name: 'Réunion', floor: 'R+1', x: 30, y: 8, width: 16, height: 22, type: 'meeting', capacity: 10, area: 20 },
    { id: 'X103', name: 'Bureau', floor: 'R+1', x: 48, y: 8, width: 14, height: 22, type: 'office', capacity: 4, area: 19 },
    { id: 'X104', name: 'Bureau', floor: 'R+1', x: 64, y: 8, width: 14, height: 22, type: 'office', capacity: 4, area: 19 },
    { id: 'X105', name: 'Bureau', floor: 'R+1', x: 80, y: 8, width: 14, height: 22, type: 'office', capacity: 4, area: 19 },
    { id: 'X106', name: 'Bureau', floor: 'R+1', x: 96, y: 8, width: 16, height: 22, type: 'office', capacity: 6, area: 37 },
    { id: 'X107', name: 'Bureau', floor: 'R+1', x: 114, y: 8, width: 16, height: 22, type: 'office', capacity: 6, area: 37 },
    { id: 'X108', name: 'Salle', floor: 'R+1', x: 132, y: 8, width: 20, height: 22, type: 'classroom', capacity: 20, area: 63 },
    { id: 'X109', name: 'Salle', floor: 'R+1', x: 154, y: 8, width: 20, height: 22, type: 'classroom', capacity: 18, area: 55 },
    { id: 'X110', name: 'Salle', floor: 'R+1', x: 176, y: 8, width: 18, height: 22, type: 'classroom', capacity: 20, area: 50 },
    { id: 'ASC1', name: 'Asc', floor: 'R+1', x: 30, y: 60, width: 10, height: 16, type: 'utility', capacity: 0, area: 5 },
    { id: 'REPRO1', name: 'Repro', floor: 'R+1', x: 42, y: 60, width: 12, height: 16, type: 'utility', capacity: 2, area: 5 },
    { id: 'X112', name: 'Salle', floor: 'R+1', x: 90, y: 58, width: 22, height: 24, type: 'classroom', capacity: 15, area: 30 },
    { id: 'WCF1', name: 'WC F', floor: 'R+1', x: 114, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 10 },
    { id: 'WCH1', name: 'WC H', floor: 'R+1', x: 128, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 16 },
    { id: 'X111', name: 'Salle', floor: 'R+1', x: 142, y: 58, width: 18, height: 24, type: 'classroom', capacity: 10, area: 25 },
    { id: 'NUMERILAB', name: 'Numérillab', floor: 'R+1', x: 162, y: 58, width: 18, height: 24, type: 'lab', capacity: 15, area: 47 },
    { id: 'FABLAB', name: 'FabLab', floor: 'R+1', x: 182, y: 58, width: 14, height: 24, type: 'lab', capacity: 12, area: 43 },
    { id: 'HALL1', name: 'Couloir', floor: 'R+1', x: 30, y: 32, width: 166, height: 24, type: 'common', capacity: 50, area: 200 },

    // ============ R+2 - Deuxième étage ============
    { id: 'X201', name: 'Open Space', floor: 'R+2', x: 4, y: 8, width: 24, height: 48, type: 'office', capacity: 40, area: 109 },
    { id: 'X202', name: 'Salle', floor: 'R+2', x: 30, y: 8, width: 16, height: 22, type: 'classroom', capacity: 12, area: 28 },
    { id: 'X203', name: 'Soutenance', floor: 'R+2', x: 48, y: 8, width: 14, height: 22, type: 'meeting', capacity: 6, area: 13 },
    { id: 'X204', name: 'Soutenance', floor: 'R+2', x: 64, y: 8, width: 14, height: 22, type: 'meeting', capacity: 6, area: 13 },
    { id: 'X205', name: 'Bureau', floor: 'R+2', x: 80, y: 8, width: 14, height: 22, type: 'office', capacity: 3, area: 12 },
    { id: 'X206', name: 'Bureau', floor: 'R+2', x: 96, y: 8, width: 14, height: 22, type: 'office', capacity: 3, area: 12 },
    { id: 'X207', name: 'Bureau', floor: 'R+2', x: 112, y: 8, width: 16, height: 22, type: 'office', capacity: 4, area: 18 },
    { id: 'X208', name: 'Bureau', floor: 'R+2', x: 130, y: 8, width: 16, height: 22, type: 'office', capacity: 4, area: 18 },
    { id: 'DETENTE', name: 'Détente', floor: 'R+2', x: 148, y: 8, width: 18, height: 22, type: 'common', capacity: 15, area: 29 },
    { id: 'X209', name: 'Salle', floor: 'R+2', x: 168, y: 8, width: 26, height: 22, type: 'classroom', capacity: 20, area: 45 },
    { id: 'ASC2', name: 'Asc', floor: 'R+2', x: 30, y: 60, width: 10, height: 16, type: 'utility', capacity: 0, area: 5 },
    { id: 'REPRO2', name: 'Repro', floor: 'R+2', x: 42, y: 60, width: 12, height: 16, type: 'utility', capacity: 2, area: 5 },
    { id: 'X210', name: 'Salle', floor: 'R+2', x: 56, y: 58, width: 22, height: 24, type: 'classroom', capacity: 10, area: 26 },
    { id: 'WCHA', name: 'WC H', floor: 'R+2', x: 90, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 12 },
    { id: 'WCFA', name: 'WC F', floor: 'R+2', x: 104, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 13 },
    { id: 'WCF2', name: 'WC F', floor: 'R+2', x: 118, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 16 },
    { id: 'WCH2', name: 'WC H', floor: 'R+2', x: 132, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 16 },
    { id: 'OPENSPACE2', name: 'Open Space', floor: 'R+2', x: 148, y: 58, width: 24, height: 24, type: 'office', capacity: 35, area: 98 },
    { id: 'HALL2', name: 'Couloir', floor: 'R+2', x: 30, y: 32, width: 164, height: 24, type: 'common', capacity: 50, area: 200 }
  ])

  // Sensors placed in rooms - NOW SYNCED FROM API
  const sensors = ref([])
  const cacheKey = 'campus-iot-placed-sensors-cache'

  // Available sensor types for drag & drop
  const sensorTypes = ref([
    { type: 'temperature', icon: 'mdi-thermometer', color: '#ff6b6b', name: 'Température' },
    { type: 'humidity', icon: 'mdi-water-percent', color: '#4ecdc4', name: 'Humidité' },
    { type: 'presence', icon: 'mdi-motion-sensor', color: '#fbbf24', name: 'Présence' },
    { type: 'co2', icon: 'mdi-molecule-co2', color: '#22c55e', name: 'CO2' },
    { type: 'light', icon: 'mdi-lightbulb', color: '#f59e0b', name: 'Luminosité' }
  ])

  // Getters
  const currentFloorRooms = computed(() => 
    rooms.value.filter(r => r.floor === currentFloor.value)
  )

  const currentFloorSensors = computed(() => 
    sensors.value.filter(s => {
      const room = rooms.value.find(r => r.id === s.room_id)
      return room && room.floor === currentFloor.value
    })
  )

  const getRoomSensors = computed(() => (roomId) => 
    sensors.value.filter(s => s.room_id === roomId)
  )

  const getRoomById = computed(() => (roomId) => 
    rooms.value.find(r => r.id === roomId)
  )

  // Stats
  const totalRooms = computed(() => rooms.value.length)
  const totalSensors = computed(() => sensors.value.length)
  const onlineSensors = computed(() => sensors.value.filter(s => s.status === 'ok').length)

  // =============================================
  // API ACTIONS - Synced with Supabase
  // =============================================

  // Fetch all placed sensors from API
  async function fetchSensors() {
    loading.value = true
    try {
      const response = await axios.get('/api/placed-sensors/')
      sensors.value = response.data.map(s => ({
        id: s.id,
        type: s.sensor_type,
        roomId: s.room_id,
        room_id: s.room_id,
        x: s.position_x,
        y: s.position_y,
        z: s.position_z,
        name: s.name,
        value: s.current_value,
        status: s.status,
        placedBy: s.placed_by_email,
        lastUpdate: s.last_update
      }))
      localStorage.setItem(cacheKey, JSON.stringify({
        sensors: sensors.value,
        cachedAt: new Date().toISOString()
      }))
    } catch (e) {
      console.error('Failed to fetch placed sensors:', e)
      loadCache()
    } finally {
      loading.value = false
    }
  }

  function loadCache() {
    try {
      const raw = localStorage.getItem(cacheKey)
      if (!raw) return
      const parsed = JSON.parse(raw)
      sensors.value = parsed.sensors || []
    } catch (e) {
      console.warn('Failed to load placed sensors cache:', e)
    }
  }

  // Add sensor via API
  async function addSensor(sensor) {
    try {
      const response = await axios.post('/api/placed-sensors/', {
        room_id: sensor.roomId,
        sensor_type: sensor.type,
        position_x: sensor.x || 0,
        position_y: sensor.y || 0,
        position_z: sensor.z || 0,
        name: sensor.name
      })
      
      const newSensor = {
        id: response.data.id,
        type: response.data.sensor_type,
        roomId: response.data.room_id,
        room_id: response.data.room_id,
        x: response.data.position_x,
        y: response.data.position_y,
        z: response.data.position_z,
        name: response.data.name,
        value: response.data.current_value,
        status: response.data.status,
        placedBy: response.data.placed_by_email,
        lastUpdate: response.data.last_update
      }
      
      sensors.value.push(newSensor)
      return newSensor
    } catch (e) {
      console.error('Failed to add sensor:', e)
      return null
    }
  }

  // Update sensor position via API
  async function updateSensorPosition(sensorId, x, y, z = 0) {
    const sensor = sensors.value.find(s => s.id === sensorId)
    if (!sensor) return
    
    try {
      await axios.put(`/api/placed-sensors/${sensorId}`, {
        position_x: x,
        position_y: y,
        position_z: z
      })
      
      sensor.x = x
      sensor.y = y
      sensor.z = z
    } catch (e) {
      console.error('Failed to update sensor position:', e)
    }
  }

  // Move sensor to another room via API
  async function moveSensorToRoom(sensorId, roomId, x, y) {
    const sensor = sensors.value.find(s => s.id === sensorId)
    if (!sensor) return
    
    try {
      // Delete old and create new (simpler than updating room_id)
      await axios.delete(`/api/placed-sensors/${sensorId}`)
      
      const response = await axios.post('/api/placed-sensors/', {
        room_id: roomId,
        sensor_type: sensor.type,
        position_x: x,
        position_y: y,
        name: sensor.name
      })
      
      // Update local
      sensor.id = response.data.id
      sensor.roomId = roomId
      sensor.room_id = roomId
      sensor.x = x
      sensor.y = y
    } catch (e) {
      console.error('Failed to move sensor:', e)
    }
  }

  // Remove sensor via API
  async function removeSensor(sensorId) {
    try {
      await axios.delete(`/api/placed-sensors/${sensorId}`)
      
      const index = sensors.value.findIndex(s => s.id === sensorId)
      if (index !== -1) {
        sensors.value.splice(index, 1)
      }
    } catch (e) {
      console.error('Failed to remove sensor:', e)
    }
  }

  // Update sensor value (from MQTT or manual)
  async function updateSensorValue(sensorId, value, status = 'ok') {
    const sensor = sensors.value.find(s => s.id === sensorId)
    if (!sensor) return
    
    try {
      await axios.put(`/api/placed-sensors/${sensorId}`, {
        current_value: value,
        status: status
      })
      
      sensor.value = value
      sensor.status = status
      sensor.lastUpdate = new Date().toISOString()
    } catch (e) {
      console.error('Failed to update sensor value:', e)
    }
  }

  // Update sensor by type and room (for MQTT updates)
  function updateSensorByTypeAndRoom(type, roomId, value) {
    const sensor = sensors.value.find(s => s.type === type && s.room_id === roomId)
    if (sensor) {
      sensor.value = value
      sensor.status = 'ok'
      sensor.lastUpdate = new Date().toISOString()
      
      // Also update in backend (fire and forget)
      axios.put(`/api/placed-sensors/${sensor.id}`, {
        current_value: value,
        status: 'ok'
      }).catch(() => {})
    }
  }

  // Handle WebSocket sensor updates
  function handleSensorPlaced(data) {
    const exists = sensors.value.find(s => s.id === data.id)
    if (!exists) {
      sensors.value.push({
        id: data.id,
        type: data.sensor_type,
        roomId: data.room_id,
        room_id: data.room_id,
        x: data.position_x,
        y: data.position_y,
        z: data.position_z,
        name: data.name,
        value: data.current_value,
        status: data.status,
        placedBy: data.placed_by_email,
        lastUpdate: data.last_update
      })
    }
  }

  function handleSensorUpdated(data) {
    const sensor = sensors.value.find(s => s.id === data.id)
    if (sensor) {
      sensor.x = data.position_x
      sensor.y = data.position_y
      sensor.z = data.position_z
      sensor.value = data.current_value
      sensor.status = data.status
      sensor.lastUpdate = data.last_update
    }
  }

  function handleSensorRemoved(data) {
    const index = sensors.value.findIndex(s => s.id === data.sensor_id)
    if (index !== -1) {
      sensors.value.splice(index, 1)
    }
  }

  // Actions
  function setFloor(floorId) {
    currentFloor.value = floorId
  }

  return {
    currentFloor,
    loading,
    floors,
    rooms,
    sensors,
    sensorTypes,
    currentFloorRooms,
    currentFloorSensors,
    getRoomSensors,
    getRoomById,
    totalRooms,
    totalSensors,
    onlineSensors,
    loadCache,
    setFloor,
    fetchSensors,
    addSensor,
    updateSensorPosition,
    moveSensorToRoom,
    removeSensor,
    updateSensorValue,
    updateSensorByTypeAndRoom,
    handleSensorPlaced,
    handleSensorUpdated,
    handleSensorRemoved
  }
})
