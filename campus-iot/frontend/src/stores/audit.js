import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useAuditStore = defineStore('audit', () => {
  const logs = ref([])
  const loading = ref(false)

  async function fetchLogs({ limit = 100, offset = 0, action = null, entityType = null, entityId = null, userId = null } = {}) {
    loading.value = true
    try {
      const response = await axios.get('/api/audit/logs', {
        params: {
          limit,
          offset,
          action: action || undefined,
          entity_type: entityType || undefined,
          entity_id: entityId || undefined,
          user_id: userId || undefined
        }
      })
      logs.value = response.data
    } catch (e) {
      console.error('Failed to fetch audit logs:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    logs,
    loading,
    fetchLogs
  }
})
