import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAlertsStore = defineStore('alerts', () => {
  // State
  const alerts = ref([])
  const rules = ref([])
  const loading = ref(false)
  const error = ref(null)
  const cacheKey = 'campus-iot-alerts-cache'

  // Getters
  const activeAlerts = computed(() => 
    alerts.value.filter(a => !a.is_acknowledged)
  )

  const alertsByPriority = computed(() => ({
    danger: activeAlerts.value.filter(a => a.severity === 'danger'),
    warning: activeAlerts.value.filter(a => a.severity === 'warning'),
    info: activeAlerts.value.filter(a => a.severity === 'info')
  }))

  const activeCount = computed(() => activeAlerts.value.length)

  // Actions
  async function fetchAlerts(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/alerts', { params })
      alerts.value = response.data
      localStorage.setItem(cacheKey, JSON.stringify({
        alerts: alerts.value,
        cachedAt: new Date().toISOString()
      }))
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch alerts:', e)
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
      alerts.value = parsed.alerts || []
    } catch (e) {
      console.warn('Failed to load alerts cache:', e)
    }
  }

  async function fetchRules() {
    try {
      const response = await axios.get('/api/alerts/rules')
      rules.value = response.data
    } catch (e) {
      console.error('Failed to fetch alert rules:', e)
    }
  }

  async function createRule(payload) {
    try {
      const response = await axios.post('/api/alerts/rules', payload)
      rules.value.unshift(response.data)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.detail || e.message }
    }
  }

  async function updateRule(ruleId, payload) {
    try {
      const response = await axios.patch(`/api/alerts/rules/${ruleId}`, payload)
      const idx = rules.value.findIndex(r => r.id === ruleId)
      if (idx !== -1) rules.value[idx] = response.data
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.detail || e.message }
    }
  }

  async function deleteRule(ruleId) {
    try {
      await axios.delete(`/api/alerts/rules/${ruleId}`)
      rules.value = rules.value.filter(r => r.id !== ruleId)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.detail || e.message }
    }
  }

  async function acknowledgeAlert(alertId) {
    try {
      await axios.post(`/api/alerts/${alertId}/ack`)
      const alert = alerts.value.find(a => a.id === alertId)
      if (alert) {
        alert.is_acknowledged = true
        alert.acknowledged_at = new Date().toISOString()
      }
    } catch (e) {
      console.error('Failed to acknowledge alert:', e)
    }
  }

  async function acknowledgeAll() {
    try {
      await axios.post('/api/alerts/ack-all')
      alerts.value.forEach(a => {
        a.is_acknowledged = true
        a.acknowledged_at = new Date().toISOString()
      })
    } catch (e) {
      console.error('Failed to acknowledge all alerts:', e)
    }
  }

  function addAlert(alert) {
    alerts.value.unshift(alert)
  }

  return {
    alerts,
    rules,
    loading,
    error,
    activeAlerts,
    alertsByPriority,
    activeCount,
    loadCache,
    fetchAlerts,
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    acknowledgeAlert,
    acknowledgeAll,
    addAlert
  }
})
