import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useBuildingStore = defineStore('building', () => {
  // Current floor
  const currentFloor = ref('RDC')
  
  // Building floors definition (3 levels: RDC, R+1, R+2)
  const floors = ref([
    { id: 'RDC', name: 'Rez-de-chaussée', level: 0 },
    { id: 'R+1', name: 'Premier étage', level: 1 },
    { id: 'R+2', name: 'Deuxième étage', level: 2 }
  ])

  // Rooms definition based on real Orion building plan (CESI Nancy)
  // Layout: Long rectangular building, rooms along a central corridor
  // Coordinates for SVG viewBox 200x100
  const rooms = ref([
    // ============ RDC - Rez-de-chaussée ============
    // Côté NORD (haut du plan) - de gauche à droite
    { id: 'X001', name: 'Accueil CESI', floor: 'RDC', x: 4, y: 8, width: 20, height: 22, type: 'common', capacity: 10, area: 29 },
    { id: 'X002', name: 'Bureau', floor: 'RDC', x: 26, y: 8, width: 16, height: 22, type: 'office', capacity: 4, area: 19 },
    { id: 'X003', name: 'Salle', floor: 'RDC', x: 44, y: 8, width: 20, height: 22, type: 'classroom', capacity: 15, area: 34 },
    { id: 'X004', name: 'Bureau', floor: 'RDC', x: 66, y: 8, width: 16, height: 22, type: 'office', capacity: 4, area: 12 },
    { id: 'X005', name: 'Salle', floor: 'RDC', x: 84, y: 8, width: 20, height: 22, type: 'classroom', capacity: 15, area: 30 },
    { id: 'X006', name: 'Salle', floor: 'RDC', x: 106, y: 8, width: 20, height: 22, type: 'classroom', capacity: 12, area: 27 },
    { id: 'X007', name: 'Salle 03', floor: 'RDC', x: 128, y: 8, width: 24, height: 22, type: 'classroom', capacity: 20, area: 38 },
    
    // Côté SUD (bas du plan) - de gauche à droite
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
    { id: 'X008', name: 'Détente élèves', floor: 'RDC', x: 156, y: 56, width: 38, height: 26, type: 'common', capacity: 30, area: 43 },
    
    // Couloir central RDC (aligné avec Hall CESI)
    { id: 'HALL_RDC', name: 'Couloir', floor: 'RDC', x: 26, y: 32, width: 168, height: 22, type: 'common', capacity: 50, area: 200 },

    // ============ R+1 - Premier étage ============
    // Côté NORD (haut du plan) - de gauche à droite
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
    
    // Côté SUD (bas du plan) - de gauche à droite
    { id: 'ASC1', name: 'Asc', floor: 'R+1', x: 30, y: 60, width: 10, height: 16, type: 'utility', capacity: 0, area: 5 },
    { id: 'REPRO1', name: 'Repro', floor: 'R+1', x: 42, y: 60, width: 12, height: 16, type: 'utility', capacity: 2, area: 5 },
    { id: 'X112', name: 'Salle', floor: 'R+1', x: 90, y: 58, width: 22, height: 24, type: 'classroom', capacity: 15, area: 30 },
    { id: 'WCF1', name: 'WC F', floor: 'R+1', x: 114, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 10 },
    { id: 'WCH1', name: 'WC H', floor: 'R+1', x: 128, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 16 },
    { id: 'X111', name: 'Salle', floor: 'R+1', x: 142, y: 58, width: 18, height: 24, type: 'classroom', capacity: 10, area: 25 },
    { id: 'NUMERILAB', name: 'Numérillab', floor: 'R+1', x: 162, y: 58, width: 18, height: 24, type: 'lab', capacity: 15, area: 47 },
    { id: 'FABLAB', name: 'FabLab', floor: 'R+1', x: 182, y: 58, width: 14, height: 24, type: 'lab', capacity: 12, area: 43 },
    
    // Couloir central R+1
    { id: 'HALL1', name: 'Couloir', floor: 'R+1', x: 30, y: 32, width: 166, height: 24, type: 'common', capacity: 50, area: 200 },

    // ============ R+2 - Deuxième étage ============
    // Côté NORD (haut du plan) - de gauche à droite
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
    
    // Côté SUD (bas du plan) - de gauche à droite
    { id: 'ASC2', name: 'Asc', floor: 'R+2', x: 30, y: 60, width: 10, height: 16, type: 'utility', capacity: 0, area: 5 },
    { id: 'REPRO2', name: 'Repro', floor: 'R+2', x: 42, y: 60, width: 12, height: 16, type: 'utility', capacity: 2, area: 5 },
    { id: 'X210', name: 'Salle', floor: 'R+2', x: 56, y: 58, width: 22, height: 24, type: 'classroom', capacity: 10, area: 26 },
    { id: 'WCHA', name: 'WC H', floor: 'R+2', x: 90, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 12 },
    { id: 'WCFA', name: 'WC F', floor: 'R+2', x: 104, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 13 },
    { id: 'WCF2', name: 'WC F', floor: 'R+2', x: 118, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 16 },
    { id: 'WCH2', name: 'WC H', floor: 'R+2', x: 132, y: 60, width: 12, height: 16, type: 'utility', capacity: 0, area: 16 },
    { id: 'OPENSPACE2', name: 'Open Space', floor: 'R+2', x: 148, y: 58, width: 24, height: 24, type: 'office', capacity: 35, area: 98 },
    
    // Couloir central R+2
    { id: 'HALL2', name: 'Couloir', floor: 'R+2', x: 30, y: 32, width: 164, height: 24, type: 'common', capacity: 50, area: 200 }
  ])

  // Sensors placed in rooms (empty by default, populated via MQTT or manual placement)
  const sensors = ref([])

  // Available sensor types for drag & drop (no pressure)
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
      const room = rooms.value.find(r => r.id === s.roomId)
      return room && room.floor === currentFloor.value
    })
  )

  const getRoomSensors = computed(() => (roomId) => 
    sensors.value.filter(s => s.roomId === roomId)
  )

  const getRoomById = computed(() => (roomId) => 
    rooms.value.find(r => r.id === roomId)
  )

  // Stats
  const totalRooms = computed(() => rooms.value.length)
  const totalSensors = computed(() => sensors.value.length)
  const onlineSensors = computed(() => sensors.value.filter(s => s.status === 'ok').length)

  // Actions
  function setFloor(floorId) {
    currentFloor.value = floorId
  }

  function addSensor(sensor) {
    const newSensor = {
      id: `${sensor.type}-${sensor.roomId}-${Date.now()}`,
      ...sensor,
      value: null,
      status: 'pending'
    }
    sensors.value.push(newSensor)
    return newSensor
  }

  function updateSensorPosition(sensorId, x, y) {
    const sensor = sensors.value.find(s => s.id === sensorId)
    if (sensor) {
      sensor.x = x
      sensor.y = y
    }
  }

  function moveSensorToRoom(sensorId, roomId, x, y) {
    const sensor = sensors.value.find(s => s.id === sensorId)
    if (sensor) {
      sensor.roomId = roomId
      sensor.x = x
      sensor.y = y
    }
  }

  function removeSensor(sensorId) {
    const index = sensors.value.findIndex(s => s.id === sensorId)
    if (index !== -1) {
      sensors.value.splice(index, 1)
    }
  }

  function updateSensorValue(sensorId, value, status = 'ok') {
    const sensor = sensors.value.find(s => s.id === sensorId)
    if (sensor) {
      sensor.value = value
      sensor.status = status
      sensor.lastUpdate = new Date().toISOString()
    }
  }

  // Update sensor by type and room (for MQTT updates)
  function updateSensorByTypeAndRoom(type, roomId, value) {
    const sensor = sensors.value.find(s => s.type === type && s.roomId === roomId)
    if (sensor) {
      sensor.value = value
      sensor.status = 'ok'
      sensor.lastUpdate = new Date().toISOString()
    }
  }

  return {
    currentFloor,
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
    setFloor,
    addSensor,
    updateSensorPosition,
    moveSensorToRoom,
    removeSensor,
    updateSensorValue,
    updateSensorByTypeAndRoom
  }
})
