import { ref, onMounted, onUnmounted } from 'vue'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'
import { useBuildingStore } from '@/stores/building'
import { useSettingsStore } from '@/stores/settings'
import { useActivityStore } from '@/stores/activity'

// Global message listeners
const messageListeners = new Set()

export function useWebSocket() {
  const ws = ref(null)
  const connected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5

  const sensorsStore = useSensorsStore()
  const alertsStore = useAlertsStore()
  const buildingStore = useBuildingStore()
  const settingsStore = useSettingsStore()
  const activityStore = useActivityStore()

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('WebSocket connected')
      connected.value = true
      reconnectAttempts.value = 0
    }

    ws.value.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleMessage(message)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.value.onclose = () => {
      console.log('WebSocket disconnected')
      connected.value = false
      attemptReconnect()
    }

    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  function handleMessage(message) {
    switch (message.type) {
      case 'sensor_data':
        sensorsStore.updateSensorValue(
          message.data.sensor_type,
          message.data.value,
          message.data.timestamp
        )
        // Also update placed sensor if exists
        if (message.data.room_id) {
          buildingStore.updateSensorByTypeAndRoom(
            message.data.sensor_type,
            message.data.room_id,
            message.data.value
          )
        }
        break
      
      case 'alert':
        alertsStore.addAlert(message.data)
        break

      case 'alert_rules_changed':
        alertsStore.fetchRules()
        break
      
      case 'actuator_status':
        // Handle actuator updates
        break
      
      // ============ SYNC EVENTS ============
      
      // Placed sensors sync
      case 'sensor_placed':
        buildingStore.handleSensorPlaced(message.sensor)
        break
      
      case 'sensor_updated':
        buildingStore.handleSensorUpdated(message.sensor)
        break
      
      case 'sensor_removed':
        buildingStore.handleSensorRemoved(message)
        break

      case 'sensor_energy_updated':
        buildingStore.handleSensorEnergyUpdated(message)
        break
      
      case 'sensors_bulk_placed':
        // Refresh all sensors
        buildingStore.fetchSensors()
        break
      
      // Settings sync
      case 'setting_changed':
      case 'system_setting_updated':
        settingsStore.handleSettingChanged(message)
        // Notify all listeners
        messageListeners.forEach(listener => listener(message))
        break
      
      case 'settings_bulk_changed':
        // Refresh all settings
        settingsStore.fetchSettings()
        break
      
      case 'actuator_command':
        // Notify listeners about new actuator command
        messageListeners.forEach(listener => listener(message))
        break
      
      case 'activity_log':
        // New activity log received - update store
        activityStore.handleNewLog(message.log)
        break
      
      default:
        console.log('Unknown message type:', message.type)
        // Still notify listeners for custom handling
        messageListeners.forEach(listener => listener(message))
    }
  }

  function attemptReconnect() {
    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
      console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.value})`)
      setTimeout(connect, delay)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  function send(data) {
    if (ws.value && connected.value) {
      ws.value.send(JSON.stringify(data))
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  // Subscribe to messages
  function onMessage(callback) {
    messageListeners.add(callback)
    // Return unsubscribe function
    return () => {
      messageListeners.delete(callback)
    }
  }

  return {
    connected,
    send,
    disconnect,
    reconnect: connect,
    onMessage
  }
}
