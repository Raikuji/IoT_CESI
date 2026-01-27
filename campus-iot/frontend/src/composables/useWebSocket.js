import { ref, onMounted, onUnmounted } from 'vue'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'

export function useWebSocket() {
  const ws = ref(null)
  const connected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5

  const sensorsStore = useSensorsStore()
  const alertsStore = useAlertsStore()

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
        break
      
      case 'alert':
        alertsStore.addAlert(message.data)
        // Could trigger a notification here
        break
      
      case 'actuator_status':
        // Handle actuator updates
        break
      
      default:
        console.log('Unknown message type:', message.type)
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

  return {
    connected,
    send,
    disconnect,
    reconnect: connect
  }
}
