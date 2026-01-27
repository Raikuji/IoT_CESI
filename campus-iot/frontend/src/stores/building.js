import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useBuildingStore = defineStore('building', () => {
  // Current floor
  const currentFloor = ref('R+1')
  
  // Building floors definition (R+1 and R+2 only)
  const floors = ref([
    { id: 'R+1', name: 'Premier étage', level: 1 },
    { id: 'R+2', name: 'Deuxième étage', level: 2 }
  ])

  // Rooms definition based on real Orion building plan (CESI Nancy)
  // Layout: Long rectangular building, rooms along a central corridor
  // Coordinates are percentages (0-100) for responsive SVG
  const rooms = ref([
    // ============ R+1 - Premier étage ============
    // Côté NORD (haut du plan) - de gauche à droite
    { id: 'X101', name: 'Open Space', floor: 'R+1', x: 3, y: 8, width: 12, height: 35, type: 'office', capacity: 40, area: 111 },
    { id: 'X102', name: 'Salle de réunion', floor: 'R+1', x: 16, y: 8, width: 6, height: 18, type: 'meeting', capacity: 10, area: 20 },
    { id: 'X103', name: 'Bureau', floor: 'R+1', x: 23, y: 8, width: 6, height: 18, type: 'office', capacity: 4, area: 19 },
    { id: 'X104', name: 'Bureau', floor: 'R+1', x: 30, y: 8, width: 6, height: 18, type: 'office', capacity: 4, area: 19 },
    { id: 'X105', name: 'Bureau', floor: 'R+1', x: 37, y: 8, width: 6, height: 18, type: 'office', capacity: 4, area: 19 },
    { id: 'X106', name: 'Bureau', floor: 'R+1', x: 44, y: 8, width: 8, height: 18, type: 'office', capacity: 6, area: 37 },
    { id: 'X107', name: 'Bureau', floor: 'R+1', x: 53, y: 8, width: 8, height: 18, type: 'office', capacity: 6, area: 37 },
    { id: 'X108', name: 'Salle', floor: 'R+1', x: 62, y: 8, width: 10, height: 18, type: 'classroom', capacity: 20, area: 63 },
    { id: 'X109', name: 'Salle', floor: 'R+1', x: 73, y: 8, width: 10, height: 18, type: 'classroom', capacity: 18, area: 55 },
    
    // Côté SUD (bas du plan) - de gauche à droite
    { id: 'ASC1', name: 'Ascenseur', floor: 'R+1', x: 16, y: 55, width: 4, height: 12, type: 'utility', capacity: 0, area: 5 },
    { id: 'REPRO1', name: 'Repro', floor: 'R+1', x: 21, y: 55, width: 5, height: 12, type: 'utility', capacity: 2, area: 5 },
    { id: 'X112', name: 'Salle', floor: 'R+1', x: 44, y: 55, width: 10, height: 20, type: 'classroom', capacity: 15, area: 30 },
    { id: 'WCF1', name: 'WC Femmes', floor: 'R+1', x: 55, y: 55, width: 5, height: 12, type: 'utility', capacity: 0, area: 10 },
    { id: 'WCH1', name: 'WC Hommes', floor: 'R+1', x: 61, y: 55, width: 5, height: 12, type: 'utility', capacity: 0, area: 16 },
    { id: 'X111', name: 'Salle', floor: 'R+1', x: 67, y: 55, width: 8, height: 20, type: 'classroom', capacity: 10, area: 25 },
    { id: 'NUMERILAB', name: 'Numérillab', floor: 'R+1', x: 76, y: 55, width: 8, height: 20, type: 'lab', capacity: 15, area: 47 },
    { id: 'DATACENTER', name: 'Data Center', floor: 'R+1', x: 85, y: 55, width: 4, height: 12, type: 'utility', capacity: 0, area: 4 },
    { id: 'FABLAB', name: 'FabLab B', floor: 'R+1', x: 90, y: 55, width: 7, height: 20, type: 'lab', capacity: 12, area: 43 },
    { id: 'X110', name: 'Salle', floor: 'R+1', x: 84, y: 8, width: 13, height: 18, type: 'classroom', capacity: 20, area: 50 },
    
    // Couloir central R+1
    { id: 'HALL1', name: 'Couloir', floor: 'R+1', x: 16, y: 28, width: 81, height: 25, type: 'common', capacity: 50, area: 200 },

    // ============ R+2 - Deuxième étage ============
    // Côté NORD (haut du plan) - de gauche à droite
    { id: 'X201', name: 'Open Space', floor: 'R+2', x: 3, y: 8, width: 12, height: 35, type: 'office', capacity: 40, area: 109 },
    { id: 'X202', name: 'Salle', floor: 'R+2', x: 16, y: 8, width: 7, height: 18, type: 'classroom', capacity: 12, area: 28 },
    { id: 'X203', name: 'Soutenance', floor: 'R+2', x: 24, y: 8, width: 6, height: 18, type: 'meeting', capacity: 6, area: 13 },
    { id: 'X204', name: 'Soutenance', floor: 'R+2', x: 31, y: 8, width: 6, height: 18, type: 'meeting', capacity: 6, area: 13 },
    { id: 'X205', name: 'Bureau', floor: 'R+2', x: 38, y: 8, width: 6, height: 18, type: 'office', capacity: 3, area: 12 },
    { id: 'X206', name: 'Bureau', floor: 'R+2', x: 45, y: 8, width: 6, height: 18, type: 'office', capacity: 3, area: 12 },
    { id: 'X207', name: 'Bureau', floor: 'R+2', x: 52, y: 8, width: 7, height: 18, type: 'office', capacity: 4, area: 18 },
    { id: 'X208', name: 'Bureau', floor: 'R+2', x: 60, y: 8, width: 7, height: 18, type: 'office', capacity: 4, area: 18 },
    { id: 'DETENTE', name: 'Détente salarié', floor: 'R+2', x: 68, y: 8, width: 8, height: 18, type: 'common', capacity: 15, area: 29 },
    { id: 'X209', name: 'Salle', floor: 'R+2', x: 77, y: 8, width: 10, height: 18, type: 'classroom', capacity: 20, area: 45 },
    { id: 'OPENSPACE2', name: 'Open Space', floor: 'R+2', x: 88, y: 8, width: 9, height: 35, type: 'office', capacity: 35, area: 98 },
    
    // Côté SUD (bas du plan) - de gauche à droite
    { id: 'ASC2', name: 'Ascenseur', floor: 'R+2', x: 16, y: 55, width: 4, height: 12, type: 'utility', capacity: 0, area: 5 },
    { id: 'REPRO2', name: 'Repro', floor: 'R+2', x: 21, y: 55, width: 5, height: 12, type: 'utility', capacity: 2, area: 5 },
    { id: 'X210', name: 'Salle', floor: 'R+2', x: 27, y: 55, width: 10, height: 20, type: 'classroom', capacity: 10, area: 26 },
    { id: 'WCHA', name: 'WC H agents', floor: 'R+2', x: 44, y: 55, width: 5, height: 12, type: 'utility', capacity: 0, area: 12 },
    { id: 'WCFA', name: 'WC F agents', floor: 'R+2', x: 50, y: 55, width: 5, height: 12, type: 'utility', capacity: 0, area: 13 },
    { id: 'WCF2', name: 'WC Femmes', floor: 'R+2', x: 56, y: 55, width: 5, height: 12, type: 'utility', capacity: 0, area: 16 },
    { id: 'WCH2', name: 'WC Hommes', floor: 'R+2', x: 62, y: 55, width: 5, height: 12, type: 'utility', capacity: 0, area: 16 },
    
    // Couloir central R+2
    { id: 'HALL2', name: 'Couloir', floor: 'R+2', x: 16, y: 28, width: 81, height: 25, type: 'common', capacity: 50, area: 200 }
  ])

  // Sensors placed in rooms
  const sensors = ref([
    // Default sensors in some rooms for demo
    { id: 'temp-x101', type: 'temperature', roomId: 'X101', x: 50, y: 30, name: 'Température Open Space', value: 22.5, unit: '°C', status: 'ok' },
    { id: 'hum-x101', type: 'humidity', roomId: 'X101', x: 70, y: 30, name: 'Humidité Open Space', value: 45, unit: '%', status: 'ok' },
    { id: 'pres-x101', type: 'presence', roomId: 'X101', x: 50, y: 70, name: 'Présence Open Space', value: 1, unit: '', status: 'ok' },
    
    { id: 'temp-x108', type: 'temperature', roomId: 'X108', x: 50, y: 40, name: 'Température Salle X108', value: 21.8, unit: '°C', status: 'ok' },
    { id: 'pres-x108', type: 'presence', roomId: 'X108', x: 50, y: 70, name: 'Présence Salle X108', value: 0, unit: '', status: 'ok' },
    
    { id: 'temp-numerilab', type: 'temperature', roomId: 'NUMERILAB', x: 50, y: 40, name: 'Température Numérillab', value: 23.2, unit: '°C', status: 'ok' },
    { id: 'hum-numerilab', type: 'humidity', roomId: 'NUMERILAB', x: 70, y: 40, name: 'Humidité Numérillab', value: 42, unit: '%', status: 'ok' },
    
    { id: 'temp-fablab', type: 'temperature', roomId: 'FABLAB', x: 50, y: 40, name: 'Température FabLab', value: 24.1, unit: '°C', status: 'ok' },
    
    { id: 'temp-x201', type: 'temperature', roomId: 'X201', x: 50, y: 30, name: 'Température Open Space R+2', value: 22.0, unit: '°C', status: 'ok' },
    { id: 'pres-x201', type: 'presence', roomId: 'X201', x: 50, y: 70, name: 'Présence Open Space R+2', value: 1, unit: '', status: 'ok' }
  ])

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
