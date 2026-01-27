import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useActivityStore = defineStore('activity', () => {
  const logs = ref([])
  const loading = ref(false)

  // Actions types with icons and colors
  const actionTypes = {
    login: { icon: 'mdi-login', color: '#22c55e', label: 'Connexion' },
    logout: { icon: 'mdi-logout', color: '#64748b', label: 'Déconnexion' },
    sensor_add: { icon: 'mdi-plus-circle', color: '#3b82f6', label: 'Capteur ajouté' },
    sensor_remove: { icon: 'mdi-minus-circle', color: '#ef4444', label: 'Capteur retiré' },
    alert_triggered: { icon: 'mdi-bell-alert', color: '#f59e0b', label: 'Alerte déclenchée' },
    alert_resolved: { icon: 'mdi-bell-check', color: '#22c55e', label: 'Alerte résolue' },
    command_sent: { icon: 'mdi-send', color: '#8b5cf6', label: 'Commande envoyée' },
    user_created: { icon: 'mdi-account-plus', color: '#22c55e', label: 'Utilisateur créé' },
    user_updated: { icon: 'mdi-account-edit', color: '#3b82f6', label: 'Utilisateur modifié' },
    user_deleted: { icon: 'mdi-account-remove', color: '#ef4444', label: 'Utilisateur supprimé' },
    role_changed: { icon: 'mdi-shield-edit', color: '#f59e0b', label: 'Rôle modifié' },
    settings_changed: { icon: 'mdi-cog', color: '#64748b', label: 'Paramètres modifiés' },
    export_data: { icon: 'mdi-download', color: '#06b6d4', label: 'Export données' }
  }

  // Add a log entry (also sends to backend)
  async function addLog(action, details = {}, userId = null) {
    const logEntry = {
      id: Date.now(),
      action,
      details,
      user_id: userId,
      timestamp: new Date().toISOString(),
      ...actionTypes[action]
    }
    
    logs.value.unshift(logEntry)
    
    // Keep only last 100 logs locally
    if (logs.value.length > 100) {
      logs.value = logs.value.slice(0, 100)
    }

    // Send to backend
    try {
      await axios.post('/api/activity/log', {
        action,
        details: JSON.stringify(details)
      })
    } catch (e) {
      console.error('Failed to log activity:', e)
    }

    return logEntry
  }

  // Fetch logs from backend
  async function fetchLogs(limit = 50) {
    loading.value = true
    try {
      const response = await axios.get('/api/activity/logs', {
        params: { limit }
      })
      logs.value = response.data.map(log => ({
        ...log,
        ...actionTypes[log.action]
      }))
    } catch (e) {
      console.error('Failed to fetch logs:', e)
    } finally {
      loading.value = false
    }
  }

  // Get logs by action type
  const getLogsByType = computed(() => (type) => {
    return logs.value.filter(log => log.action === type)
  })

  // Get recent logs
  const recentLogs = computed(() => logs.value.slice(0, 20))

  return {
    logs,
    loading,
    actionTypes,
    addLog,
    fetchLogs,
    getLogsByType,
    recentLogs
  }
})
