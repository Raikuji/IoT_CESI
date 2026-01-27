import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useSensorsStore = defineStore('sensors', () => {
  // State
  const sensors = ref([])
  const loading = ref(false)
  const error = ref(null)
  const lastUpdate = ref(null)

  // Getters
  const getSensorByType = computed(() => (type) => {
    return sensors.value.find(s => s.type === type)
  })

  const temperature = computed(() => getSensorByType.value('temperature'))
  const humidity = computed(() => getSensorByType.value('humidity'))
  const pressure = computed(() => getSensorByType.value('pressure'))
  const presence = computed(() => getSensorByType.value('presence'))
  const co2 = computed(() => getSensorByType.value('co2'))

  const onlineSensors = computed(() => 
    sensors.value.filter(s => s.status === 'ok' || s.status === 'warning')
  )

  // Actions
  async function fetchSensors() {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/sensors')
      sensors.value = response.data
      lastUpdate.value = new Date()
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch sensors:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchSensorData(sensorId, params = {}) {
    try {
      const response = await axios.get(`/api/sensors/${sensorId}/data`, { params })
      return response.data
    } catch (e) {
      console.error('Failed to fetch sensor data:', e)
      return []
    }
  }

  function updateSensorValue(sensorType, value, timestamp) {
    const sensor = sensors.value.find(s => s.type === sensorType)
    if (sensor) {
      sensor.latest_value = value
      sensor.latest_time = timestamp
      sensor.status = 'ok'
      lastUpdate.value = new Date()
    }
  }

  return {
    sensors,
    loading,
    error,
    lastUpdate,
    temperature,
    humidity,
    pressure,
    presence,
    co2,
    onlineSensors,
    fetchSensors,
    fetchSensorData,
    updateSensorValue
  }
})
